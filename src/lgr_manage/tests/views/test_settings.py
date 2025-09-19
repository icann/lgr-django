from http import HTTPStatus

from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_web.config import get_lgr_settings


class TestToolSettings(LgrWebClientTestBase):
    settings_url = '/m/settings'

    def setUp(self):
        super().setUp()
        self.lgr_settings = get_lgr_settings()
        self.lgr_settings.refresh_from_db()

    def test_access_when_logged_in_as_admin(self):
        self.login_admin()

        response = self.client.get('/m/settings')

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'lgr_manage/settings.html')

    def test_cannot_access_as_icann_user(self):
        self.login_icann()

        response = self.client.get(self.settings_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_access_as_regular_user(self):
        self.login_user()

        response = self.client.get(self.settings_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_access_when_not_logged_in(self):
        response = self.client.get(self.settings_url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={self.settings_url}')

    def test_update_settings_as_admin(self):
        self.login_admin()
        self.assertEqual(self.lgr_settings.variant_calculation_limit, 100)
        data = {
            'variant_calculation_limit': 500,
            'variant_calculation_max': 5000,
            'variant_calculation_abort': 50000,
            'report_expiration_delay': 50
        }

        response = self.client.post('/m/settings', data=data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.lgr_settings.refresh_from_db()
        self.assertEqual(self.lgr_settings.variant_calculation_limit, 500)
        self.assertEqual(self.lgr_settings.variant_calculation_max, 5000)
        self.assertEqual(self.lgr_settings.variant_calculation_abort, 50000)
        self.assertEqual(self.lgr_settings.report_expiration_delay, 50)
