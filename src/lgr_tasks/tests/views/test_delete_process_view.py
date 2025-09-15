from unittest.mock import patch

import lgr_web.celery_app
from lgr_tasks.models import LgrTaskModel
from lgr_tasks.tests.helpers import LGRTasksClientTestBase, MockCeleryControl


@patch.object(lgr_web.celery_app.app, 'control', MockCeleryControl())
class TestDeleteProcessView(LGRTasksClientTestBase):
    def test_deletes_task_instance(self):
        self.assertTrue(LgrTaskModel.objects.filter(pk=2).exists())

        self.client.post('/tasks/2/delete')

        self.assertFalse(LgrTaskModel.objects.filter(pk=2).exists())

    def test_revokes_task_instance_with_pending_status_without_deleting(self):
        # TODO: The test uses the status REVOKED, but should also check for RETRY
        self.assertTrue(LgrTaskModel.objects.filter(pk=4).exists())

        self.client.post('/tasks/4/delete')

        self.assertTrue(LgrTaskModel.objects.filter(pk=4).exists())
        self.t4.refresh_from_db()
        self.assertEquals('REVOKED', self.t4.name)
