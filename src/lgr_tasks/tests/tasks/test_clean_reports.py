import datetime
from io import StringIO

from lgr_advanced.api import LGRToolReportStorage
from lgr_idn_table_review.icann_tools.api import LGRIcannReportStorage
from lgr_idn_table_review.idn_tool.api import LGRIdnReviewApi
from lgr_manage.api import LGRAdminReportStorage
from lgr_models.models.report import LGRReport
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_tasks.tasks import clean_reports
from lgr_web.config import get_lgr_settings


class TestCleanReports(LgrWebClientTestBase):
    def test_deletes_reports_after_expiration_delay_and_are_not_icann_reports(self):
        # Save fake user generated report
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
        self.assertListEqual(
            sorted(list(LGRReport.objects.values_list('pk', flat=True))),
            [report1.pk, report2.pk, report3.pk, report4.pk, report5.pk])

        clean_reports()

        # Unexpired reports should still be there along with ICANN reports
        self.assertListEqual(
            sorted(list(LGRReport.objects.values_list('pk', flat=True))),
            [report3.pk, report5.pk])
