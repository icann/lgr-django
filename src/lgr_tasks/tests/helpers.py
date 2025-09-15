import os
from datetime import timedelta
from io import BytesIO

from django.core.files import File
from django.utils import timezone

from lgr_models.models.report import LGRReport
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_session.views import StorageType
from lgr_tasks.models import LgrTaskModel


class MockCeleryInspect:
    def active(self):
        return {'test': [{'id': 3}]}

    def reserved(self):
        return {'test': [{'id': 4}]}

    def scheduled(self):
        return {'test': []}

    def revoked(self):
        return {'test': [2]}


class MockCeleryControl:
    def inspect(self):
        return MockCeleryInspect()

    def revoke(self, task_id, terminate):
        LgrTaskModel.objects.filter(pk=task_id).update(name='REVOKED')


class MockCeleryAsyncResult:
    def __init__(self, task_id) -> None:
        self.task_id = task_id
        super().__init__()

    @property
    def status(self):
        if self.task_id == 6:
            return 'TESTING'
        return 'PENDING'


class LGRTasksClientTestBase(LgrWebClientTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.maxDiff = None

        self.user = self.login_admin()

        self.t1 = LgrTaskModel.objects.create(
            id=1,
            app='test',
            name='Test Task',
            creation_date=timezone.now(),
            user=self.user
        )
        self.t2 = LgrTaskModel.objects.create(
            id=2,
            app='test',
            name='Test Task',
            creation_date=timezone.now(),
            user=self.user
        )
        self.t3 = LgrTaskModel.objects.create(
            id=3,
            app='test',
            name='Test Task',
            creation_date=timezone.now(),
            user=self.user
        )
        self.t4 = LgrTaskModel.objects.create(
            id=4,
            app='test',
            name='Test Task',
            creation_date=timezone.now(),
            user=self.user
        )
        self.t5 = LgrTaskModel.objects.create(
            id=5,
            app='test',
            name='Test Task',
            creation_date=timezone.now(),
            user=self.user
        )
        self.t6 = LgrTaskModel.objects.create(
            id=6,
            app='test',
            name='Test Task',
            creation_date=timezone.now(),
            user=self.user
        )

    def given_task_expired(self, task):
        task.creation_date = timezone.now() - timedelta(hours=1, minutes=1)
        task.save()

    def given_task_completed(self, task):
        def test_upload_path(obj, instance, filename):
            return os.path.join('tmp/lgr-tools-test', filename)

        LGRReport.storage_type = StorageType.TOOL
        LGRReport.upload_path = test_upload_path

        report = LGRReport.objects.create(
            file=File(
                BytesIO(b'Testing test_get_task_info_task_with_report'),
                name=f'test_get_task_info_task_with_report.txt'),
            owner=self.user,
            report_id='test_get_task_info_task_with_report')
        task.report = report
        task.save()
        return report
