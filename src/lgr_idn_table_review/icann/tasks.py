# -*- coding: utf-8 -*-
import logging
import time
from io import BytesIO
from zipfile import ZipFile, ZIP_BZIP2

from celery import shared_task
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from lgr.exceptions import LGRException
from lgr.tools.idn_review.review import review_lgr
from lgr_idn_table_review.icann.api import get_icann_idn_repository_tables, get_reference_lgr
from lgr_idn_table_review.tool.api import IdnTableInfo

logger = logging.getLogger(__name__)


def _review_idn_table(idn_table_info):
    ref_lgr = get_reference_lgr(idn_table_info)
    if not ref_lgr:
        return None
    ref_lgr_info = IdnTableInfo.from_dict({
        'name': ref_lgr.name,
        'data': ref_lgr.file.read().decode('utf-8'),
    })
    return review_lgr(idn_table_info.lgr, ref_lgr_info.lgr)


@shared_task
def idn_table_review_task(email_address):
    """
    Review all IDN tables

    :param email_address: The e-mail address where the results will be sent
    """
    zip_content = BytesIO()
    with ZipFile(zip_content, mode='w', compression=ZIP_BZIP2) as zf:
        for tld, idn_table_info in get_icann_idn_repository_tables():
            try:
                context = _review_idn_table(idn_table_info)
            except BaseException:
                logger.exception('Failed to review IDN table')
                context = {
                    'name': idn_table_info.name,
                    'reason': 'Invalid IDN table'
                }
                html_report = render_to_string('lgr_idn_table_review_icann/not_reviewed.html', context)
            else:
                if context:
                    html_report = render_to_string('lgr_idn_table_review_tool/review.html', context)
                else:
                    context = {
                        'name': idn_table_info.name,
                        'reason': 'No Reference LGR was found to compare with IDN table'
                    }
                    html_report = render_to_string('lgr_idn_table_review_icann/not_reviewed.html', context)
            finally:
                zf.writestr(f"{tld.upper()}.{idn_table_info.lgr.metadata.languages[0]}."
                            f"{idn_table_info.lgr.metadata.version.value}.{time.strftime('%Y-%m-%d')}.html",
                            html_report)

    storage = FileSystemStorage(location=settings.IDN_REVIEW_ICANN_OUTPUT_STORAGE_LOCATION,
                                file_permissions_mode=0o440)
    filename = f"{time.strftime('%Y%m%d_%H%M%S')}_idn_report.zip"
    storage.save(filename, zip_content)

    zip_content.close()

    email = EmailMessage(subject='ICANN IDN table review completed',
                         to=[email_address])
    email.body = f"ICANN IDN table review has been successfully completed.\n" \
                 f"You should now be able to download it from your ICANN review " \
                 f"home screen under the name: '{filename}'.\n" \
                 f"Please refresh the home page if you don't see the link.\n" \
                 f"Best regards"
    email.send()
