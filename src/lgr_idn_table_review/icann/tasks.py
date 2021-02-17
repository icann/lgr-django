# -*- coding: utf-8 -*-
import logging
import os
import time
import traceback
from io import StringIO
from typing import Dict
from zipfile import ZipFile, ZIP_BZIP2

from celery import shared_task
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

from lgr.tools.idn_review.review import review_lgr
from lgr_advanced import unidb
from lgr_advanced.lgr_editor.forms import DEFAULT_UNICODE_VERSION
from lgr_idn_table_review.admin.models import RefLgr, RzLgrMember
from lgr_idn_table_review.icann.api import get_icann_idn_repository_tables, get_reference_lgr, IANA_IDN_TABLES
from lgr_idn_table_review.tool.api import IdnTableInfo
from lgr_session.views import StorageType

logger = logging.getLogger(__name__)


def _review_idn_table(context: Dict, idn_table_info, absolute_url):
    ref_lgr = get_reference_lgr(idn_table_info)
    if not ref_lgr:
        context['reason'] = 'No Reference LGR was found to compare with IDN table.'
        return None
    ref_lgr_info = IdnTableInfo.from_dict({
        'name': ref_lgr.name,
        'data': ref_lgr.file.read().decode('utf-8'),
    })
    context['ref_lgr'] = ref_lgr.name  # TODO put TLD/tag/version here instead of ref_lgr
    if isinstance(ref_lgr, RefLgr):
        context['ref_lgr_url'] = absolute_url + reverse('lgr_idn_admin_display_ref_lgr', kwargs={'lgr_id': ref_lgr.pk})
    elif isinstance(ref_lgr, RzLgrMember):
        context['ref_lgr_url'] = absolute_url + reverse('lgr_idn_admin_display_rz_lgr_member',
                                                        kwargs={'rz_lgr_id': ref_lgr.rz_lgr.pk, 'lgr_id': ref_lgr.pk})
    context.update(review_lgr(idn_table_info.lgr, ref_lgr_info.lgr))
    return ref_lgr.name


def _create_review_report(idn_table_info, absolute_url):
    html_report = ''
    context = {
        'idn_table': idn_table_info.name,
        'idn_table_url': f'{IANA_IDN_TABLES}/tables/{idn_table_info.name}'
    }
    flag = None
    ref_lgr_name = None
    try:
        ref_lgr_name = _review_idn_table(context, idn_table_info, absolute_url)
    except BaseException:
        logger.exception('Failed to review IDN table')
        context['reason'] = 'Invalid IDN table.'
        if settings.DEBUG:
            context['reason'] += f'\n{traceback.format_exc()}'
        html_report = render_to_string('lgr_idn_table_review/error.html', context)
    else:
        if ref_lgr_name:
            html_report = render_to_string('lgr_idn_table_review/review.html', context)
            flag = 1
            for result in context['summary'].values():
                if result not in ['MATCH', 'NOTE']:
                    flag = 0
                    break
        else:
            html_report = render_to_string('lgr_idn_table_review/error.html', context)
    finally:
        return html_report, ref_lgr_name, flag


@shared_task
def idn_table_review_task(absolute_url, email_address):
    """
    Review all IDN tables

    :param absolute_url: The absolute website url
    :param email_address: The e-mail address where the results will be sent
    """
    path = time.strftime('%Y-%m-%d-%H%M%S')
    storage = FileSystemStorage(location=os.path.join(settings.IDN_REVIEW_ICANN_OUTPUT_STORAGE_LOCATION, path),
                                file_permissions_mode=0o640)
    udata = unidb.manager.get_db_by_version(DEFAULT_UNICODE_VERSION)

    count = 0
    processed = []
    storage.save(f'{path}.zip', StringIO(''))
    today = time.strftime('%Y-%m-%d')
    with storage.open(f'{path}.zip', 'wb') as f:
        with ZipFile(f, mode='w', compression=ZIP_BZIP2) as zf:
            for tlds, idn_table_info in get_icann_idn_repository_tables():
                count += len(tlds)
                html_report, ref_lgr_name, flag = _create_review_report(idn_table_info, absolute_url)
                for tld in tlds:
                    tld_a_label = udata.idna_encode_label(tld)
                    # need to save a version per tld, processed and count will reflect that as well
                    lang = idn_table_info.lgr.metadata.languages[0]
                    filename = f"{tld_a_label.upper()}.{lang}." \
                               f"{idn_table_info.lgr.metadata.version.value}.{today}.html"
                    if flag is not None:
                        processed.append({
                            'name': f"{tld.upper()}.{lang}.{flag}.{ref_lgr_name}",
                            'url': absolute_url + reverse('download_file',
                                                          kwargs={
                                                              'storage': StorageType.IDN_REVIEW_ICANN_MODE.value,
                                                              'filename': filename,
                                                              'folder': path
                                                          }) + '?display=true'
                        })
                    zf.writestr(filename, html_report)
                    storage.save(filename, StringIO(html_report))

    summary_report = render_to_string('lgr_idn_table_review_icann/report.html', {
        'count': count,
        'date': today,
        'processed': processed
    })
    storage.save(f'{path}-summary.html', StringIO(summary_report))

    email = EmailMessage(subject='ICANN IDN table review completed',
                         to=[email_address])
    email.body = f"ICANN IDN table review has been successfully completed.\n" \
                 f"You should now be able to download it from your ICANN review " \
                 f"home screen under the path: '{path}'.\n" \
                 f"Please refresh the home page if you don't see the link.\n" \
                 f"Best regards"
    email.send()
