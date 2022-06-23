#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import os
from io import StringIO

from django.core.cache import cache
from django.core.files import File
from django.test import override_settings

from lgr_manage.api import LGRAdminStorage
from lgr_manage.models import AdminReport
from lgr_models.models.lgr import RzLgr
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_tasks.tasks import calculate_index_variant_labels_tlds, _index_cache_key


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
        storage = LGRAdminStorage(None)
        auto_report = storage.storage_save_report_file('test-indexes.csv', StringIO())
        # save fake user generated report to check it would not be erased
        storage = LGRAdminStorage(self.login_admin())
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
        storage = LGRAdminStorage(None)
        with self.assertRaises(AdminReport.DoesNotExist):
            storage.storage_get_report_file(auto_report.pk)
        self.assertEquals(user_report, storage.storage_get_report_file(user_report.pk))
        last_report: AdminReport = storage.list_storage().first()
        with last_report.file.open('r') as f:
            reader: csv.DictReader = csv.DictReader(f)
            self.assertListEqual(expected_report, [row for row in reader])
