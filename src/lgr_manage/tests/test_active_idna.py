import unittest
from http import HTTPStatus

from lgr_models.models.lgr import IDNARepertoire
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class IDNAActiveTestCase(LgrWebClientTestBase):
    def test_access_active_when_logged_in(self):
        self.login_admin()

        response = self.client.get('/m/idna')
        self.assertContains(response,
                            '<form class="form-horizontal" id="active-choice-form" url-data="/m/idna/isactive">',
                            status_code=HTTPStatus.OK)

    def test_access_active_when_not_logged_in(self):
        response = self.client.get('/m/idna')
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login?next=/m/idna')

    def test_update_active_when_logged_in(self):
        self.login_admin()
        self.client.post('/m/idna/isactive', data={'active': 2})
        response = self.client.post('/m/idna/isactive', data={'active': 4})
        self.assertContains(response, '"old_active": 2', status_code=HTTPStatus.OK)
        self.assertEquals(IDNARepertoire.objects.filter(active=True).first().pk, 4)

    def test_update_active_when_logged_in_notadmin(self):
        self.login_user()
        self.client.post('/m/idna/isactive', data={'active': 2})
        response = self.client.post('/m/idna/isactive', data={'active': 4})
        self.assertContains(response, status_code=HTTPStatus.UNAUTHORIZED)

    def test_update_active_when_not_logged_in(self):
        response = self.client.post('/m/idna/isactive', data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login?next=/m/idna/isactive')
