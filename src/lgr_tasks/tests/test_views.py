# -*- coding: utf-8 -*-
from unittest.mock import patch

import lgr_web.celery_app
from lgr_tasks.models import LgrTaskModel
from lgr_tasks.tests.common import TasksTestBase, MockCeleryControl


@patch.object(lgr_web.celery_app.app, 'control', MockCeleryControl())
class TestView(TasksTestBase):

    def test_delete_process(self):
        self.assertTrue(LgrTaskModel.objects.filter(pk=2).exists())
        self.client.post('/tasks/2/delete')
        self.assertFalse(LgrTaskModel.objects.filter(pk=2).exists())

    def test_delete_pending_process(self):
        self.assertTrue(LgrTaskModel.objects.filter(pk=4).exists())
        self.client.post('/tasks/4/delete')
        self.assertTrue(LgrTaskModel.objects.filter(pk=4).exists())
        self.t4.refresh_from_db()
        self.assertEquals('REVOKED', self.t4.name)

    def test_delete_finished_process(self):
        # make t1 expired
        self.given_task_expired(self.t1)
        # make t4 completed
        self.given_task_completed(self.t4)

        self.assertTrue(LgrTaskModel.objects.filter(pk__in=range(1, 6)).exists())
        self.client.post('/tasks/delete')
        self.assertFalse(LgrTaskModel.objects.filter(pk__in=[1, 2, 4]).exists())
        self.assertTrue(LgrTaskModel.objects.filter(pk__in=[3, 5]).exists())
