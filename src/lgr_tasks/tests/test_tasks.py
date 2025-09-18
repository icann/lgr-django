#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import datetime
import os
from io import StringIO

from django.core.cache import cache
from django.core.files import File
from django.test import override_settings

from lgr_advanced.api import LGRToolReportStorage
from lgr_idn_table_review.icann_tools.api import LGRIcannReportStorage
from lgr_idn_table_review.idn_tool.api import LGRIdnReviewApi
from lgr_manage.api import LGRAdminReportStorage
from lgr_manage.models import AdminReport
from lgr_models.models.lgr import RzLgr
from lgr_models.models.report import LGRReport
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_tasks.tasks import calculate_index_variant_labels_tlds, _index_cache_key, clean_reports
from lgr_web.config import get_lgr_settings


class TasksTest(LgrWebClientTestBase):
    fixtures_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures'))

    def setUp(self):
        cache.clear()
        RzLgr.objects.all().update(active=False)
        with open(os.path.join(self.fixtures_path, 'Sample-French-a-variant.xml'), 'r') as f:
            self.rz_lgr = RzLgr.objects.create(file=File(f, name='Sample-French-a-variant.xml'),
                                               name='RZ LGR Test', active=True)

    @override_settings(ICANN_TLDS=f"file://{os.path.join(fixtures_path, 'tlds.txt')}")
    def test_calculate_index_variant_labels_tlds(self):
        # save fake periodic report to check it would be correctly erased
        storage = LGRAdminReportStorage(None)
        auto_report = storage.storage_save_report_file('test-indexes.csv', StringIO())
        # save fake user generated report to check it would not be erased
        storage = LGRAdminReportStorage(self.login_admin())
        user_report = storage.storage_save_report_file('test-indexes.csv', StringIO())

        expected_indexes = {
            'abc': (0x0061, 0x0062, 0x0063),
            'àbc': (0x0061, 0x0062, 0x0063),
            'def': (0x0064, 0x0065, 0x0066),
            'ghi': 'NotInLGR',
        }
        expected_report = [
            {'Label': 'abc', 'Index': 'abc'},
            {'Label': 'àbc', 'Index': 'abc'},
            {'Label': 'def', 'Index': 'def'},
            {'Label': 'ghi', 'Index': 'NotInLGR'}
        ]

        calculate_index_variant_labels_tlds()

        self.assertDictEqual(expected_indexes, cache.get(_index_cache_key(self.rz_lgr)))
        storage = LGRAdminReportStorage(None)
        with self.assertRaises(AdminReport.DoesNotExist):
            storage.storage_get_report_file(auto_report.pk)
        self.assertEquals(user_report, storage.storage_get_report_file(user_report.pk))
        last_report: AdminReport = storage.list_storage().first()
        with last_report.file.open('rb') as f:
            # remove BOM
            data = f.read().decode('utf-8-sig')
            reader: csv.DictReader = csv.DictReader(StringIO(data))
            self.assertListEqual(expected_report, [row for row in reader])

    def test_clean_reports(self):
        # save fake user generated report
        user = self.login_user()
        last_month = datetime.datetime.now() - datetime.timedelta(days=31)
        get_lgr_settings().report_expiration_delay = 30
        storage = LGRAdminReportStorage(self.login_admin())
        report1 = storage.storage_save_report_file('test1.csv', StringIO())
        storage = LGRToolReportStorage(user)
        report2 = storage.storage_save_report_file('test2.csv', StringIO())
        report3 = storage.storage_save_report_file('test3.csv', StringIO())
        storage = LGRIdnReviewApi(user)
        report4 = storage.storage_save_report_file('test4.csv', StringIO())
        storage = LGRIcannReportStorage(self.login_icann())
        report5 = storage.storage_save_report_file('test5.csv', StringIO())
        report1.created_at = last_month
        report1.save()
        report2.created_at = last_month
        report2.save()
        report4.created_at = last_month
        report4.save()
        report5.created_at = last_month
        report5.save()
        # sanity check
        self.assertListEqual(sorted(list(LGRReport.objects.values_list('pk', flat=True))),
                             [report1.pk, report2.pk, report3.pk, report4.pk, report5.pk])

        clean_reports()

        # unexpired reports should still be there along with ICANN reports
        self.assertListEqual(sorted(list(LGRReport.objects.values_list('pk', flat=True))), [report3.pk, report5.pk])
