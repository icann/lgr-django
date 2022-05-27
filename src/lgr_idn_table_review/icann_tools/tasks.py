# -*- coding: utf-8 -*-
import json
import logging
import os
import time
import traceback
from datetime import date
from io import StringIO
from tempfile import TemporaryFile
from typing import Dict
from zipfile import ZipFile, ZIP_DEFLATED

from celery import shared_task, current_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from lgr.tools.idn_review.review import review_lgr
from lgr_auth.models import LgrUser
from lgr_idn_table_review.icann_tools.api import (get_icann_idn_repository_tables,
                                                  get_reference_lgr,
                                                  NoRefLgrFound, LGRIcannStorage)
from lgr_idn_table_review.icann_tools.models import IANAIdnTable
from lgr_models.models.unicode import UnicodeVersion
from lgr_tasks.models import LgrTaskModel
from lgr_utils import unidb

logger = logging.getLogger(__name__)


def _review_idn_table(context: Dict, idn_table: IANAIdnTable, absolute_url):
    idn_table_lgr = idn_table.to_lgr()
    ref_lgr = get_reference_lgr(idn_table_lgr)
    context['ref_lgr'] = ref_lgr.name  # TODO put TLD/tag/version here instead of ref_lgr
    context['ref_lgr_url'] = absolute_url + ref_lgr.display_url()
    context.update(review_lgr(idn_table_lgr, ref_lgr.to_lgr()))
    return ref_lgr.name


def _json_date_converter(k):
    if isinstance(k, date):
        return k.__str__()


def _create_review_report(idn_table: IANAIdnTable, absolute_url, lgr_storage, report_id):
    html_report = ''
    context = {
        'idn_table': idn_table.name,
        'idn_table_url': idn_table.download_url()
    }
    flag = None
    ref_lgr_name = None
    try:
        ref_lgr_name = _review_idn_table(context, idn_table, absolute_url)
    except NoRefLgrFound as exc:
        logger.exception('Failed to get a reference LGR')
        context['reason'] = f'No Reference LGR was found to compare with IDN table:\n{exc.message}'
        html_report = render_to_string('lgr_idn_table_review/error.html', context)
    except BaseException:
        logger.exception('Failed to review IDN table')
        context['reason'] = 'Invalid IDN table.'
        if settings.DEBUG:
            context['reason'] += f'\n{traceback.format_exc()}'
        html_report = render_to_string('lgr_idn_table_review/error.html', context)
    else:
        html_report = render_to_string('lgr_idn_table_review/review.html', context)
        flag = 1
        for result in context['summary'].values():
            if result not in ['MATCH', 'NOTE']:
                flag = 0
                break
    finally:
        if settings.DEBUG:
            json_name = f'{os.path.splitext(idn_table.name)[0]}.json'
            json_data = StringIO()
            json.dump(context, json_data, default=_json_date_converter, indent=2)
            lgr_storage.storage_save_report_file(os.path.join('json', json_name), json_data, report_id=report_id)
        return html_report, ref_lgr_name, flag


@shared_task
def idn_table_review_task(user_pk, absolute_url):
    """
    Review all IDN tables

    :param user_pk: The user primary key
    :param absolute_url: The absolute website url
    """
    report_id = timezone.now().strftime('%Y-%m-%d-%H%M%S.%f')
    user = LgrUser.objects.get(pk=user_pk)

    try:
        report = process_idn_tables(user, absolute_url, report_id)
    except Exception:
        logger.exception('ICANN IDN table review failed')
        raise
    else:
        LgrTaskModel.objects.filter(pk=current_task.request.id).update(report=report)
    return f'{user} - {report_id}.zip'


def process_idn_tables(user, absolute_url, report_id):
    udata = unidb.manager.get_db_by_version(UnicodeVersion.default().version)
    lgr_storage = LGRIcannStorage(user)
    count = 0
    processed = []
    unprocessed = []
    today = time.strftime('%Y-%m-%d')
    with TemporaryFile() as f:
        with ZipFile(f, mode='w', compression=ZIP_DEFLATED) as zf:
            for tlds, idn_table in get_icann_idn_repository_tables():
                logger.info('Process IDN table %s', idn_table.filename)
                count += len(tlds)
                html_report, ref_lgr_name, flag = _create_review_report(idn_table, absolute_url,
                                                                        lgr_storage, report_id)
                for tld in tlds:
                    lgr = idn_table.to_lgr()
                    tld_a_label = udata.idna_encode_label(tld)
                    # need to save a version per tld, processed and count will reflect that as well
                    lang = lgr.metadata.languages[0]
                    version = lgr.metadata.version.value
                    filename = f"{tld_a_label.upper()}.{lang}.{version}.{today}.html"
                    report = lgr_storage.storage_save_report_file(filename, StringIO(html_report), report_id=report_id)
                    url = f'{absolute_url}{report.to_url()}?display=true'
                    if flag is not None:
                        processed.append({
                            'name': f"{tld.upper()}.{lang}.{version}.{flag}.{idn_table.name}.{ref_lgr_name}",
                            'url': url
                        })
                    else:
                        unprocessed.append({
                            'name': f"{tld.upper()}.{lang}.{version}.0.0",
                            'url': url
                        })
                    zf.writestr(filename, html_report)
        report = lgr_storage.storage_save_report_file(f'{report_id}.zip', f, report_id=report_id)

    summary_report = render_to_string('lgr_idn_table_review_icann/summary_report.html', {
        'count': count,
        'date': today,
        'processed': processed,
        'unprocessed': unprocessed
    })
    lgr_storage.storage_save_report_file(f'{report_id}-summary.html', StringIO(summary_report),
                                         report_id=report_id)
    return report
