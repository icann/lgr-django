# -*- coding: utf-8 -*-
import logging
from io import StringIO
from tempfile import TemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED

from celery import shared_task, current_task


from lgr_auth.models import LgrUser
from lgr_idn_table_review.idn_tool.api import LGRIdnReviewApi
from lgr_tasks.models import LgrTaskModel

logger = logging.getLogger(__name__)


@shared_task
def idn_table_review_task(user_pk, idn_tables, report_id, absolute_url):
    """
    Review IDN tables

    :param user_pk: The user primary key
    :param idn_tables: The IDN table pk to review associated to their reference LGR information as a tuple
    :param report_id: The report ID
    :param absolute_url: The absolute website url
    :return:
    """
    user = LgrUser.objects.get(pk=user_pk)
    api = LGRIdnReviewApi(user)

    # ensure report_id is unique
    while api.storage_model.objects.filter(report_id=report_id).exists():
        idx = 0
        try:
            rid, i = report_id.rsplit('-', 1)
            idx = int(i)
        except:
            report_id += f'-{idx + 1}'
        else:
            report_id = f'{rid}-{idx + 1}'

    try:
        report = process_idn_tables(api, absolute_url, idn_tables, report_id)
    except Exception:
        logger.exception('IDN table review failed')
        api.delete_report(report_id)
        raise
    else:
        LgrTaskModel.objects.filter(pk=current_task.request.id).update(report=report)
    return f'{user} - {report_id}.zip'


def process_idn_tables(api, absolute_url, idn_tables, report_id):
    with TemporaryFile() as f:
        with ZipFile(f, mode='w', compression=ZIP_DEFLATED) as zf:
            for idn_table_pk, lgr_info in idn_tables:
                idn_table_name, html_report = api.create_review_report(idn_table_pk, lgr_info, absolute_url)
                filename = f"{idn_table_name}.html"
                zf.writestr(filename, html_report)
                api.storage_save_report_file(filename, StringIO(html_report), report_id=report_id)
        return api.storage_save_report_file(f'{report_id}.zip', f, report_id=report_id)
