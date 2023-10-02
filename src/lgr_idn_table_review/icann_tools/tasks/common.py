# -*- coding: utf-8 -*-
import logging
import time
from datetime import date
from io import StringIO
from tempfile import TemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED

from celery import current_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from lgr_auth.models import LgrUser
from lgr_idn_table_review.icann_tools.api import (get_icann_idn_repository_tables,
                                                  LGRIcannReportStorage)
from lgr_tasks.models import LgrTaskModel
from lgr_utils import unidb

logger = logging.getLogger(__name__)


class ICANNTask:
    task_cb = None
    report_type = None

    def __init__(self, user_pk, absolute_url):
        self.absolute_url = absolute_url
        self.report_id = f"{timezone.now().strftime('%Y-%m-%d-%H%M%S.%f')}-{self.report_type}"
        self.today = time.strftime('%Y-%m-%d')
        self.user = LgrUser.objects.get(pk=user_pk)
        self.lgr_storage = LGRIcannReportStorage(self.user)
        self.udata = unidb.manager.get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)
        self.count = 0
        self.summary_context = {
            'dl_errors_count': 0,
            'date': self.today,
            'count': 0,
            'unprocessed': [],
            'processed': [],
        }

    def __call__(self):
        return self.run_task()

    def run_task(self):
        try:
            report = self.process_idn_tables()
        except Exception:
            logger.exception('ICANN IDN table processing failed')
            raise
        else:
            LgrTaskModel.objects.filter(pk=current_task.request.id).update(report=report)
        return f'{self.user} - {self.report_id}.zip'

    def process_idn_tables(self):
        with TemporaryFile() as f:
            errors = []
            with ZipFile(f, mode='w', compression=ZIP_DEFLATED) as zf:
                for tlds, idn_table, err in get_icann_idn_repository_tables():
                    if err:
                        errors.append(err)
                        continue
                    logger.info('Process IDN table %s', idn_table.filename)
                    for filename, data in self.task_cb(idn_table, tlds):
                        zf.writestr(filename, data)

            final_report = self.lgr_storage.storage_save_report_file(f'{self.report_id}.zip', f,
                                                                     report_id=self.report_id)
            if errors:
                zf.writestr('errors.txt', '\n'.join(errors))
                self.summary_context['dl_errors_count'] = len(errors)

        summary_report = render_to_string('lgr_idn_table_review_icann/summary_report.html', self.summary_context)
        self.lgr_storage.storage_save_report_file(f'{self.report_id}-summary.html', StringIO(summary_report),
                                                  report_id=self.report_id)
        return final_report

    @staticmethod
    def _json_date_converter(k):
        if isinstance(k, date):
            return k.__str__()
