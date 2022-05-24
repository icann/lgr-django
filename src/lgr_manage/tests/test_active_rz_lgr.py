from http import HTTPStatus

from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_models.models.lgr import RzLgr


class RzLgrActiveTestCase(LgrWebClientTestBase):
    def test_access_active_when_logged_in(self):
        self.login()

        response = self.client.get('/m/rz-lgr')
        self.assertContains(response,
                            '<form class="form-horizontal" id="active-choice-form" url-data="/m/rz-lgr/isactive">',
                            status_code=HTTPStatus.OK)

    def test_access_active_when_not_logged_in(self):
        response = self.client.get('/m/rz-lgr')
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login?next=/m/rz-lgr')

    def test_update_active_when_logged_in(self):
        self.login()
        self.client.post('/m/rz-lgr/isactive', data={'active': 2})
        response = self.client.post('/m/rz-lgr/isactive', data={'active': 4})
        self.assertContains(response, '"old_active": 2', status_code=HTTPStatus.OK)
        self.assertEquals(RzLgr.objects.filter(active=True).first().pk, 4)

    def test_update_active_when_not_logged_in(self):
        response = self.client.post('/m/rz-lgr/isactive', data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login?next=/m/rz-lgr/isactive')
