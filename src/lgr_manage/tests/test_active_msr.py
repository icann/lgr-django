from http import HTTPStatus

from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_models.models.lgr import MSR


class MSRActiveTestCase(LgrWebClientTestBase):
    def test_access_active_when_logged_in(self):
        self.login()

        response = self.client.get('/m/msr')
        self.assertContains(response,
                            '<form class="form-horizontal" id="active-choice-form" url-data="/m/msr/isactive">',
                            status_code=HTTPStatus.OK)

    def test_access_active_when_not_logged_in(self):
        response = self.client.get('/m/msr')
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login?next=/m/msr')

    def test_update_active_when_logged_in(self):
        self.login()
        self.client.post('/m/msr/isactive', data={'active': 2})
        response = self.client.post('/m/msr/isactive', data={'active': 4})
        self.assertContains(response, '"old_active": 2', status_code=HTTPStatus.OK)
        self.assertEquals(MSR.objects.filter(active=True).first().pk, 4)

    def test_update_active_when_not_logged_in(self):
        response = self.client.post('/m/msr/isactive', data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login?next=/m/msr/isactive')
