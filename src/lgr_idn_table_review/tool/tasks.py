# -*- coding: utf-8 -*-
import logging
import os
import time
from ast import literal_eval
from io import StringIO
from zipfile import ZipFile, ZIP_BZIP2

from celery import shared_task
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

from lgr.tools.idn_review.review import review_lgr
from lgr_idn_table_review.admin.models import RefLgr, RzLgr
from lgr_idn_table_review.tool.api import IdnTableInfo

logger = logging.getLogger(__name__)


def _review_idn_table(report_id, idn_table_info, lgr_info):
    lgr_type, lgr_name = literal_eval(lgr_info)
    if lgr_type == 'ref':
        ref_lgr = RefLgr.objects.get(name=lgr_name)
        ref_lgr_url = reverse('lgr_idn_admin_display_ref_lgr', kwargs={'lgr_id': ref_lgr.pk})
    elif lgr_type == 'rz':
        ref_lgr = RzLgr.objects.get(name=lgr_name)
        ref_lgr_url = reverse('lgr_idn_admin_display_ref_lgr', kwargs={'lgr_id': ref_lgr.pk})
    else:
        raise BaseException
    ref_lgr_info = IdnTableInfo.from_dict({
        'name': ref_lgr.name,
        'data': ref_lgr.file.read().decode('utf-8'),
    })
    context = review_lgr(idn_table_info.lgr, ref_lgr_info.lgr)
    context['ref_lgr_url'] = ref_lgr_url
    context['idn_table_url'] = reverse('lgr_review_display_idn_table',
                                       kwargs={'report_id': report_id, 'lgr_id': idn_table_info.name})
    return context


def _create_review_report(report_id, idn_table_json, lgr_info):
    html_report = ''
    try:
        idn_table_info = IdnTableInfo.from_dict(idn_table_json)
        context = _review_idn_table(report_id, idn_table_info, lgr_info)
    except BaseException:
        logger.exception('Failed to review IDN table')
        context = {'name': idn_table_json['name']}
        html_report = render_to_string('lgr_idn_table_review/error.html', context)
    else:
        html_report = render_to_string('lgr_idn_table_review/review.html', context)
    finally:
        return html_report


@shared_task
def idn_table_review_task(idn_tables, report_id, email_address, storage_path, download_link):
    """
    Review IDN tables

    :param idn_tables: The IDN table to review in JSON format associated to their reference LGR information as a tuple
    :param report_id: The report ID
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    :param download_link: The link where the file will be available
    :return:
    """
    path = time.strftime('%Y-%m-%d-%H%M%S')
    storage = FileSystemStorage(location=os.path.join(storage_path, path),
                                file_permissions_mode=0o640)

    storage.save(f'{path}.zip', StringIO(''))
    with storage.open(f'{path}.zip', 'wb') as f:
        with ZipFile(f, mode='w', compression=ZIP_BZIP2) as zf:
            for idn_table_json, lgr_info in idn_tables:
                html_report = _create_review_report(report_id, idn_table_json, lgr_info)
                filename = f"{idn_table_json['name']}.html"
                zf.writestr(filename, html_report)
                storage.save(filename, StringIO(html_report))

    if email_address:
        email = EmailMessage(subject='IDN table review',
                             to=[email_address])
        email.body = f"IDN table review has been successfully completed.\n" \
                     f"You should now be able to download it from {download_link} under the path: '{path}'.\n" \
                     f"Please refresh the home page if you don't see the link.\n" \
                     f"Best regards"
        email.send()
