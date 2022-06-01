# -*- coding: utf-8 -*-
from unittest.mock import patch

import lgr_web.celery_app
from lgr_tasks.api import get_task_info
from lgr_tasks.tests.common import TasksTestBase, MockCeleryControl, MockCeleryAsyncResult


@patch.object(lgr_web.celery_app.Celery, 'control', MockCeleryControl())
@patch.object(lgr_web.celery_app.Celery, 'AsyncResult', MockCeleryAsyncResult)
class TestTasksApi(TasksTestBase):

    def setUp(self) -> None:
        super().setUp()
        self.maxDiff = None

    def test_get_task_info(self):
        task_info = get_task_info(self.user)
        self.assertListEqual(task_info, [{
            'id': 1,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t1.creation_date,
            'report': None,
            'status': 'PENDING',
        }, {
            'id': 2,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t2.creation_date,
            'report': None,
            'status': 'REVOKED',
        }, {
            'id': 3,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t3.creation_date,
            'report': None,
            'status': 'STARTED',
        }, {
            'id': 4,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t4.creation_date,
            'report': None,
            'status': 'PENDING',
        }, {
            'id': 5,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t5.creation_date,
            'report': None,
            'status': 'PENDING',
        }, {
            'id': 6,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t6.creation_date,
            'report': None,
            'status': 'TESTING',
        }])

    def test_get_task_info_expired_task(self):
        # t1 would show as expired
        # t5 would show as pending as there is an active task created before
        for task in [self.t1, self.t2, self.t3, self.t4, self.t5]:
            self.given_task_expired(task)

        task_info = get_task_info(self.user)
        self.assertListEqual(task_info, [{
            'id': 1,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t1.creation_date,
            'report': None,
            'status': 'EXPIRED',
        }, {
            'id': 2,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t2.creation_date,
            'report': None,
            'status': 'REVOKED',
        }, {
            'id': 3,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t3.creation_date,
            'report': None,
            'status': 'STARTED',
        }, {
            'id': 4,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t4.creation_date,
            'report': None,
            'status': 'PENDING',
        }, {
            'id': 5,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t5.creation_date,
            'report': None,
            'status': 'PENDING',
        }, {
            'id': 6,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t6.creation_date,
            'report': None,
            'status': 'TESTING',
        }])

    def test_get_task_info_task_with_report(self):
        report = self.given_task_completed(self.t1)

        task_info = get_task_info(self.user)
        self.assertListEqual(task_info, [{
            'id': 1,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t1.creation_date,
            'report': report,
            'status': 'SUCCESS',
        }, {
            'id': 2,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t2.creation_date,
            'report': None,
            'status': 'REVOKED',
        }, {
            'id': 3,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t3.creation_date,
            'report': None,
            'status': 'STARTED',
        }, {
            'id': 4,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t4.creation_date,
            'report': None,
            'status': 'PENDING',
        }, {
            'id': 5,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t5.creation_date,
            'report': None,
            'status': 'PENDING',
        }, {
            'id': 6,
            'app': 'test',
            'name': 'Test Task',
            'creation_date': self.t6.creation_date,
            'report': None,
            'status': 'TESTING',
        }])
