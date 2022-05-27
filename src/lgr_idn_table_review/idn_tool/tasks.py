# -*- coding: utf-8 -*-
import logging
from io import StringIO
from tempfile import TemporaryFile
from typing import Dict
from zipfile import ZipFile, ZIP_DEFLATED

from celery import shared_task, current_task
from django.template.loader import render_to_string

from lgr.tools.idn_review.review import review_lgr
from lgr_auth.models import LgrUser
from lgr_idn_table_review.idn_tool.api import LGRIdnReviewApi
from lgr_idn_table_review.idn_tool.models import IdnTable
from lgr_models.models.lgr import LgrBaseModel
from lgr_tasks.models import LgrTaskModel

logger = logging.getLogger(__name__)


def _review_idn_table(context: Dict, idn_table: IdnTable, lgr_info, absolute_url):
    ref_lgr = LgrBaseModel.from_tuple(lgr_info)
    context.update({
        'ref_lgr': ref_lgr.name,
        'ref_lgr_url': absolute_url + ref_lgr.display_url()
    })
    context.update(review_lgr(idn_table.to_lgr(), ref_lgr.to_lgr()))


def _create_review_report(idn_table: IdnTable, lgr_info, absolute_url):
    html_report = ''
    context = {
        'idn_table': idn_table.name,
        'idn_table_url': absolute_url + idn_table.display_url()
    }
    try:
        _review_idn_table(context, idn_table, lgr_info, absolute_url)
    except BaseException:
        logger.exception('Failed to review IDN table')
        html_report = render_to_string('lgr_idn_table_review/error.html', context)
    else:
        html_report = render_to_string('lgr_idn_table_review/review.html', context)
    finally:
        return html_report


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
                idn_table = api.get_lgr(idn_table_pk)
                html_report = _create_review_report(idn_table, lgr_info, absolute_url)
                filename = f"{idn_table.name}.html"
                zf.writestr(filename, html_report)
                api.storage_save_report_file(filename, StringIO(html_report), report_id=report_id)
        return api.storage_save_report_file(f'{report_id}.zip', f, report_id=report_id)
