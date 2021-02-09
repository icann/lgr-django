# -*- coding: utf-8 -*-
import logging
import time
from ast import literal_eval
from io import BytesIO
from zipfile import ZipFile, ZIP_BZIP2

from celery import shared_task
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from lgr.tools.idn_review.review import review_lgr
from lgr_idn_table_review.admin.models import RefLgr, RzLgr, LgrModel
from lgr_idn_table_review.tool.api import IdnTableInfo

logger = logging.getLogger(__name__)


def _review_idn_table(idn_table_info, lgr_info):
    lgr_type, lgr_name = literal_eval(lgr_info)
    try:
        if lgr_type == 'ref':
            ref_lgr = RefLgr.objects.get(name=lgr_name)
        elif lgr_type == 'rz':
            ref_lgr = RzLgr.objects.get(name=lgr_name)
        else:
            return None
    except LgrModel.DoesNotExist:
        return None
    ref_lgr_info = IdnTableInfo.from_dict({
        'name': ref_lgr.name,
        'data': ref_lgr.file.read().decode('utf-8'),
    })
    return review_lgr(idn_table_info.lgr, ref_lgr_info.lgr)


@shared_task
def idn_table_review_task(idn_tables, email_address, storage_path, download_link):
    """
    Review IDN tables

    :param idn_tables: The IDN table to review in JSON format associated to their reference LGR information as a tuple
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    :param download_link: The link where the file will be available
    :return:
    """
    zip_content = BytesIO()
    with ZipFile(zip_content, mode='w', compression=ZIP_BZIP2) as zf:
        for idn_table_json, lgr_info in idn_tables:
            try:
                idn_table_info = IdnTableInfo.from_dict(idn_table_json)
                context = _review_idn_table(idn_table_info, lgr_info)
                if not context:
                    raise BaseException
            except BaseException:
                logger.exception('Failed to review IDN table')
                context = {'name': idn_table_json['name']}
                html_report = render_to_string('lgr_idn_table_review_tool/error.html', context)
            else:
                html_report = render_to_string('lgr_idn_table_review_tool/review.html', context)
            finally:
                zf.writestr(f"{idn_table_json['name']}.html", html_report)

    storage = FileSystemStorage(location=storage_path,
                                file_permissions_mode=0o440)
    filename = f"{time.strftime('%Y%m%d_%H%M%S')}_idn_table_review.zip"
    storage.save(filename, zip_content)

    zip_content.close()

    if email_address:
        email = EmailMessage(subject='IDN table review',
                             to=[email_address])
        email.body = f"IDN table review has been successfully completed.\n" \
                     f"You should now be able to download it from {download_link} under the name: '{filename}'.\n" \
                     f"Please refresh the home page if you don't see the link.\n" \
                     f"Best regards"
        email.send()
