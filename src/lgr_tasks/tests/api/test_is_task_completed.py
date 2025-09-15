from unittest.mock import patch

import lgr_web.celery_app
from lgr_tasks.api import is_task_completed
from lgr_tasks.tests.helpers import LGRTasksClientTestBase, MockCeleryAsyncResult, MockCeleryControl


@patch.object(lgr_web.celery_app.app, 'control', MockCeleryControl())
@patch.object(lgr_web.celery_app.app, 'AsyncResult', MockCeleryAsyncResult)
class TestIsTaskCompleted(LGRTasksClientTestBase):
    def test_returns_status_of_existing_tasks(self):
        self.given_task_completed(self.t1)

        self.assertTrue(is_task_completed(1))
        self.assertTrue(is_task_completed(2))
        self.assertFalse(is_task_completed(3))
        self.assertFalse(is_task_completed(4))
        self.assertFalse(is_task_completed(5))
        self.assertTrue(is_task_completed(6))
