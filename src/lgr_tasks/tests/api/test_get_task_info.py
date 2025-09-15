from unittest.mock import patch

import lgr_web.celery_app
from lgr_tasks.api import get_task_info
from lgr_tasks.tests.helpers import LGRTasksClientTestBase, MockCeleryAsyncResult, MockCeleryControl


@patch.object(lgr_web.celery_app.app, 'control', MockCeleryControl())
@patch.object(lgr_web.celery_app.app, 'AsyncResult', MockCeleryAsyncResult)
class TestGetTaskInfo(LGRTasksClientTestBase):
    def test_returns_info_for_each_tasks(self):
        task_info = get_task_info(self.user)
        self.assertListEqual(
            task_info,
            [{
                'id': 1,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t1.creation_date,
                'report': None,
                'status': 'PENDING'
            }, {
                'id': 2,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t2.creation_date,
                'report': None,
                'status': 'REVOKED'
            }, {
                'id': 3,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t3.creation_date,
                'report': None,
                'status': 'STARTED'
            }, {
                'id': 4,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t4.creation_date,
                'report': None,
                'status': 'PENDING'
            }, {
                'id': 5,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t5.creation_date,
                'report': None,
                'status': 'PENDING'
            }, {
                'id': 6,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t6.creation_date,
                'report': None,
                'status': 'TESTING'
            }]
        )

    def test_returns_info_for_expired_tasks(self):
        # t1 would show as expired
        # t5 would show as pending as there is an active task created before
        for task in [self.t1, self.t2, self.t3, self.t4, self.t5]:
            self.given_task_expired(task)

        task_info = get_task_info(self.user)
        self.assertListEqual(
            task_info,
            [{
                'id': 1,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t1.creation_date,
                'report': None,
                'status': 'EXPIRED'
            }, {
                'id': 2,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t2.creation_date,
                'report': None,
                'status': 'REVOKED'
            }, {
                'id': 3,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t3.creation_date,
                'report': None,
                'status': 'STARTED'
            }, {
                'id': 4,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t4.creation_date,
                'report': None,
                'status': 'PENDING'
            }, {
                'id': 5,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t5.creation_date,
                'report': None,
                'status': 'PENDING'
            }, {
                'id': 6,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t6.creation_date,
                'report': None,
                'status': 'TESTING'
            }]
        )

    def test_return_task_info_with_report(self):
        report = self.given_task_completed(self.t1)

        task_info = get_task_info(self.user)
        self.assertListEqual(
            task_info,
            [{
                'id': 1,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t1.creation_date,
                'report': report,
                'status': 'SUCCESS'
            }, {
                'id': 2,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t2.creation_date,
                'report': None,
                'status': 'REVOKED'
            }, {
                'id': 3,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t3.creation_date,
                'report': None,
                'status': 'STARTED'
            }, {
                'id': 4,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t4.creation_date,
                'report': None,
                'status': 'PENDING'
            }, {
                'id': 5,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t5.creation_date,
                'report': None,
                'status': 'PENDING'
            }, {
                'id': 6,
                'app': 'test',
                'name': 'Test Task',
                'creation_date': self.t6.creation_date,
                'report': None,
                'status': 'TESTING'
            }]
        )
