# -*- coding: utf-8 -*-
import json
import logging
import os
import traceback
from io import StringIO
from typing import Dict

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string

from lgr.tools.idn_review.review import review_lgr
from lgr_idn_table_review.icann_tools.api import (get_reference_lgr,
                                                  NoRefLgrFound)
from lgr_idn_table_review.icann_tools.models import IANAIdnTable
from lgr_idn_table_review.icann_tools.tasks.common import ICANNTask

logger = logging.getLogger(__name__)


@shared_task
def idn_table_review_task(user_pk, absolute_url):
    """
    Review all IDN tables

    :param user_pk: The user primary key
    :param absolute_url: The absolute website url
    """
    return IDNTableReviewTask(user_pk, absolute_url)()


class IDNTableReviewTask(ICANNTask):
    report_type = 'review'

    def __init__(self, user_pk, absolute_url):
        super().__init__(user_pk, absolute_url)
        self.task_cb = self._idn_table_review
        self.summary_context.update({
            'title': 'ICANN IDN Table Review summary'
        })

    def _idn_table_review(self, idn_table, tlds):
        self.summary_context['count'] += len(tlds)
        html_report, ref_lgr_name, flag, invalid_table = self._create_review_report(idn_table)
        for tld in tlds:
            _, lang, version = idn_table.name.split('_', 3)
            tld_a_label = self.udata.idna_encode_label(tld)
            if not invalid_table:
                lgr = idn_table.to_lgr()
                # need to save a version per tld, processed and count will reflect that as well
                lang = lgr.metadata.languages[0]
                version = lgr.metadata.version.value
            filename = f"{tld_a_label.upper()}.{lang}.{version}.{self.today}.html"
            report = self.lgr_storage.storage_save_report_file(filename, StringIO(html_report), report_id=self.report_id)
            url = f'{self.absolute_url}{report.to_url()}?display=true'
            if flag is not None:
                self.summary_context['processed'].append({
                    'name': f"{tld.upper()}.{lang}.{version}.{flag}.{idn_table.name}.{ref_lgr_name}",
                    'url': url
                })
            else:
                self.summary_context['unprocessed'].append({
                    'name': f"{tld.upper()}.{lang}.{version}.0.0",
                    'url': url
                })
            data = html_report

            yield filename, data

    def _create_review_report(self, idn_table: IANAIdnTable):
        html_report = ''
        context = {
            'idn_table': idn_table.name,
            'idn_table_url': idn_table.download_url()
        }
        flag = None
        ref_lgr_name = None
        invalid_table = False
        try:
            ref_lgr_name = self._review_idn_table(context, idn_table)
        except NoRefLgrFound as exc:
            logger.exception('Failed to get a reference LGR')
            context['reason'] = f'No Reference LGR was found to compare with IDN table:\n{exc.message}'
            html_report = render_to_string('lgr_idn_table_review/error.html', context)
        except Exception:
            logger.exception('Failed to review IDN table')
            context['reason'] = 'Invalid IDN table.'
            invalid_table = True
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
                json.dump(context, json_data, default=self._json_date_converter, indent=2)
                self.lgr_storage.storage_save_report_file(os.path.join('json', json_name), json_data, report_id=self.report_id)
            return html_report, ref_lgr_name, flag, invalid_table

    def _review_idn_table(self, context: Dict, idn_table: IANAIdnTable):
        idn_table_lgr = idn_table.to_lgr()
        ref_lgr = get_reference_lgr(idn_table_lgr)
        context['ref_lgr'] = ref_lgr.name  # TODO put TLD/tag/version here instead of ref_lgr
        context['ref_lgr_url'] = self.absolute_url + ref_lgr.display_url()
        context.update(review_lgr(idn_table_lgr, ref_lgr.to_lgr()))
        return ref_lgr.name
