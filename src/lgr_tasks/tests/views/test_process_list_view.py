from unittest.mock import patch

import lgr_web.celery_app
from lgr_tasks.tests.helpers import LGRTasksClientTestBase, MockCeleryControl


@patch.object(lgr_web.celery_app.app, 'control', MockCeleryControl())
class TestView(LGRTasksClientTestBase):
    def test_returns_ordered_list_of_tasks(self):
        response = self.client.get('/tasks/list')

        self.assertTemplateUsed(response, 'lgr_tasks/process_list.html')
        self.assertIn('tasks', response.context_data)
        # We cannot assert the content of response.context_data['tasks']
        # since it is a `list_reverseiterator`, which gets consumed when
        # rendering the view.

    @patch('lgr_tasks.views.get_task_info')
    def test_returns_error_message_when_unable_to_retrieve_tasks(self, mock_get_task_info):
        mock_get_task_info.side_effect = Exception

        response = self.client.get('/tasks/list')

        self.assertTemplateUsed(response, 'lgr_tasks/process_list.html')
        self.assertNotIn('tasks', response.context_data)
        self.assertContains(response, 'Unable to retrieve the list of tasks.')
