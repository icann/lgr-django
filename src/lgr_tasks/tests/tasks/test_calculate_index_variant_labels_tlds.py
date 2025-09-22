import csv
import os
from io import StringIO
from pathlib import Path

from django.core.cache import cache
from django.core.files import File
from django.test import override_settings

from lgr_manage.api import LGRAdminReportStorage
from lgr_manage.models import AdminReport
from lgr_models.models.lgr import RzLgr
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_tasks.tasks import _index_cache_key, calculate_index_variant_labels_tlds


class TestCalculateIndexVariantLabelsTLDs(LgrWebClientTestBase):
    fixtures_path = Path(__file__).resolve().parent.parent / 'fixtures'

    def setUp(self):
        cache.clear()
        RzLgr.objects.all().update(active=False)
        with open(os.path.join(self.fixtures_path, 'Sample-French-a-variant.xml'), 'r') as f:
            self.rz_lgr = RzLgr.objects.create(
                file=File(f, name='Sample-French-a-variant.xml'), name='RZ LGR Test', active=True)

    @override_settings(ICANN_TLDS=f"file://{os.path.join(fixtures_path, 'tlds.txt')}")
    def test_calculate_index_variant_labels_tlds(self):
        # Save fake periodic report to check it would be correctly erased
        storage = LGRAdminReportStorage(None)
        auto_report = storage.storage_save_report_file('test-indexes.csv', StringIO())
        # Save fake user generated report to check it would not be erased
        storage = LGRAdminReportStorage(self.login_admin())
        user_report = storage.storage_save_report_file('test-indexes.csv', StringIO())

        expected_indexes = {
            'abc': (0x0061, 0x0062, 0x0063),
            'àbc': (0x0061, 0x0062, 0x0063),
            'def': (0x0064, 0x0065, 0x0066),
            'ghi': 'NotInLGR'}
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
            # Remove BOM
            data = f.read().decode('utf-8-sig')
            reader: csv.DictReader = csv.DictReader(StringIO(data))
            self.assertListEqual(expected_report, [row for row in reader])
