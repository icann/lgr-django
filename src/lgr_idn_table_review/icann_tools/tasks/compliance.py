# -*- coding: utf-8 -*-
import logging
import traceback
from io import StringIO

from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string

from lgr.tools.idna2008_compliance import check_idna2008_compliance
from lgr_idn_table_review.icann_tools.tasks.common import ICANNTask

logger = logging.getLogger(__name__)


@shared_task
def idn_table_compliance_task(user_pk, absolute_url):
    """
    Check all IDN tables for IDNA 2008 non-compliance

    :param user_pk: The user primary key
    :param absolute_url: The absolute website url
    """
    return IDNTableIDNA2008ComplianceTask(user_pk, absolute_url)()


class IDNTableIDNA2008ComplianceTask(ICANNTask):
    report_type = 'idna2008-compliance'

    def __init__(self, user_pk, absolute_url):
        super().__init__(user_pk, absolute_url)
        self.task_cb = self._idn_table_check_compliance
        self.summary_context.update({
            'idna_compliance_valid': 0,
            'title': 'ICANN IDN Table IDNA 2008 compliance summary'
        })

    def _idn_table_check_compliance(self, idn_table, tlds):
        self.summary_context['count'] += len(tlds)
        generate_report = True
        context = {}
        idn_table_lgr = None
        try:
            context.update({
                'idn_table': idn_table.name,
                'idn_table_url': idn_table.download_url()
            })
            idn_table_lgr = idn_table.to_lgr()
            context['uncompliant_cps'] = check_idna2008_compliance(idn_table_lgr)
            html_report = render_to_string('lgr_idn_table_review_icann/idna2008_compliance.html', context)
            generate_report = len(context['uncompliant_cps']) > 0
            if not generate_report:
                self.summary_context['idna_compliance_valid'] += 1
        except BaseException:
            logger.exception('Failed to review IDN table')
            context['reason'] = 'Invalid IDN table.'
            if settings.DEBUG:
                context['reason'] += f'\n{traceback.format_exc()}'
            html_report = render_to_string('lgr_idn_table_review/error.html', context)

        for tld in tlds:
            if not generate_report:
                continue

            _, lang, version = idn_table.name.split('_', 3)
            tld_a_label = self.udata.idna_encode_label(tld)
            # need to save a version per tld, processed and count will reflect that as well
            if idn_table_lgr:
                lang = idn_table_lgr.metadata.languages[0]
                version = idn_table_lgr.metadata.version.value
            filename = f"{tld_a_label.upper()}.{lang}.{version}.{self.today}.html"
            report = self.lgr_storage.storage_save_report_file(filename, StringIO(html_report),
                                                               report_id=self.report_id)
            url = f'{self.absolute_url}{report.to_url()}?display=true'
            if idn_table_lgr:
                self.summary_context['processed'].append({
                    'name': f"{tld.upper()}.{lang}.{version}.{idn_table.name}",
                    'url': url
                })
            else:
                self.summary_context['unprocessed'].append({
                    'name': f"{tld.upper()}.{lang}.{version}.{idn_table.name}",
                    'url': url
                })
            data = html_report

            yield filename, data
