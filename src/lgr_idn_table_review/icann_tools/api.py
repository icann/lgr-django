#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import logging
import os
from collections import defaultdict
from urllib.request import urlopen

import lxml.html
from django.conf import settings
from django.core.files import File

from lgr.core import LGR
from lgr.tools.utils import download_file
from lgr.utils import tag_to_language_script
from lgr_auth.models import LgrRole
from lgr_idn_table_review.icann_tools.models import IdnReviewIcannReport, IANAIdnTable
from lgr_models.models.lgr import RefLgr, RzLgrMember, RzLgr
from lgr_session.api import LGRStorage

logger = logging.getLogger(__name__)

IDN_TABLES_SESSION_KEY = 'idn-table'
IANA_URL = 'https://www.iana.org'
IANA_IDN_TABLES = IANA_URL + '/domains/idn-tables'


class NoRefLgrFound(BaseException):

    def __init__(self, msg):
        self.message = msg


class LGRIcannStorage(LGRStorage):
    storage_model = IdnReviewIcannReport

    def __init__(self, user):
        super().__init__(user, filter_on_user=False)

    def storage_can_read(self):
        return self.user.role in [LgrRole.ICANN.value, LgrRole.ADMIN.value]


def get_icann_idn_repository_tables():
    tree = lxml.html.parse(urlopen(IANA_IDN_TABLES))
    idn_table_columns = tree.xpath("//table[@id='idn-table']/tbody/tr")

    # some urls are the same for many TLDs therefore need to loop twice to regroup them instead of parsing multiple
    # times the same LGR
    urls = defaultdict(set)
    dates = {}
    for col in idn_table_columns:
        a_tag = col.findall('td/a')[0]
        tld = a_tag.find('span').text.strip('.')
        url = a_tag.attrib['href'].strip()
        date = col.findall('td')[3].text.strip()
        urls[url].add(tld)
        dates.setdefault(url, date)

    for url, tlds in urls.items():
        basename = os.path.basename(url)
        if settings.ICANN_IDN_REVIEW_TABLES and basename not in settings.ICANN_IDN_REVIEW_TABLES:
            continue
        __, lang_script, version = basename.rsplit('.', 1)[0].split('_', 3)
        date = dates.get(url)
        name, data = download_file(IANA_URL + url)
        idn_table = IANAIdnTable(file=File(data, name=name),
                                 name=os.path.splitext(name)[0],
                                 owner=None,
                                 url=IANA_URL + url,
                                 date=date,
                                 lang_script=lang_script,
                                 version=version)
        yield tlds, idn_table


def _make_lgr_query(obj, q, logs, multiple_found_query=None):
    obj_name = 'Reference LGR'
    if obj == RzLgrMember:
        obj_name = 'RZ LGR'

    query_str = ', '.join(f"{k.split('__')[0]}={v or ''}" for k, v in q.items())

    logger.info("Look for %s LGR with query %s", obj.__name__, q)
    try:
        ref = obj.objects.get(**q)
        logger.info('Found reference LGR %s', ref.name)
        return ref
    except obj.DoesNotExist:
        logger.warning("No reference LGR found")
        logs.append(f"No {obj_name} found for {query_str}")
        return None
    except obj.MultipleObjectsReturned:
        logger.info("Multiple reference LGR found")
        logs.append(f"More than one {obj_name} found for {query_str}")
        if multiple_found_query:
            return _make_lgr_query(obj, multiple_found_query, logs)
        return None


def get_reference_lgr(idn_table: IANAIdnTable):
    lgr: LGR = idn_table.to_lgr()
    logger.info('Look for reference LGR for IDN table %s', idn_table.name)
    logs = []
    try:
        tag = lgr.metadata.languages[0]
    except IndexError:
        logger.warning("No language tag in IDN table %s", lgr)
        raise NoRefLgrFound("No language tag in IDN table")

    language, script = tag_to_language_script(tag, use_suppress_script=True)
    logger.info("Look for reference LGR with language '%s' and script '%s'", language, script)
    if language:
        if script:
            ref_lgr = _make_lgr_query(RefLgr, {'language__iexact': language, 'script__iexact': script}, logs)
        else:
            ref_lgr = _make_lgr_query(RefLgr, {'language__iexact': language, 'script__iexact': ''}, logs)
        if ref_lgr:
            return ref_lgr

    # get the latest RZ LGR (XXX: we assume they are all named the same with an increasing ID)
    last_rz_lgr = RzLgr.objects.order_by('-name').first()

    if script:
        logger.info("Look for Ref. LGR then RZ LGR for script '%s'", script)
        ref_lgr = _make_lgr_query(RefLgr, {'script__iexact': script, 'language': ''}, logs)
        if ref_lgr:
            return ref_lgr
        rz_lgr = _make_lgr_query(RzLgrMember,
                                 {'script__iexact': script,
                                  'language': '',
                                  'rz_lgr__name': last_rz_lgr.name},
                                 logs)
        if rz_lgr:
            return rz_lgr

    if not last_rz_lgr:
        logger.info("No RZ LGR")
        raise NoRefLgrFound('\n'.join(logs))

    if language:
        logger.info("Look for RZ LGR with language '%s'", language)
        if script:
            rz_lgr = _make_lgr_query(RzLgrMember,
                                     {'language__iexact': language,
                                      'script__iexact': script,
                                      'rz_lgr__name': last_rz_lgr.name},
                                     logs)
        else:
            rz_lgr = _make_lgr_query(RzLgrMember, {'language__iexact': language, 'rz_lgr__name': last_rz_lgr.name},
                                     logs, multiple_found_query={'language__iexact': language,
                                                                 'script__iexact': '',
                                                                 'rz_lgr__name': last_rz_lgr.name})
        if rz_lgr:
            return rz_lgr

    raise NoRefLgrFound('\n'.join(logs))
