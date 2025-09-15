from unittest.mock import patch

import lgr_web.celery_app
from lgr_tasks.models import LgrTaskModel
from lgr_tasks.tests.helpers import LGRTasksClientTestBase, MockCeleryControl


@patch.object(lgr_web.celery_app.app, 'control', MockCeleryControl())
class TestDeleteAllFinishedProcessesView(LGRTasksClientTestBase):
    def test_deletes_all_finished_task_instance(self):
        # make t1 expired
        self.given_task_expired(self.t1)
        # make t4 completed
        self.given_task_completed(self.t4)
        self.assertTrue(LgrTaskModel.objects.filter(pk__in=range(1, 6)).exists())

        self.client.post('/tasks/delete')

        self.assertFalse(LgrTaskModel.objects.filter(pk__in=[1, 2, 4]).exists())
        self.assertTrue(LgrTaskModel.objects.filter(pk__in=[3, 5]).exists())
