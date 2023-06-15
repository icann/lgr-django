from http import HTTPStatus

from django.urls import reverse

from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_web.config import lgr_settings


class TestSettings(LgrWebClientTestBase):

    def setUp(self):
        super().setUp()
        lgr_settings.refresh_from_db()

    def test_settings_user_unauthorized(self):
        self.login_user()

        response = self.client.get(reverse('lgr_admin_settings'))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_settings_icann_unauthorized(self):
        self.login_icann()

        response = self.client.get(reverse('lgr_admin_settings'))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_settings_when_not_logged_in(self):
        response = self.client.get(reverse('lgr_admin_settings'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={reverse("lgr_admin_settings")}')

    def test_settings_tab(self):
        self.login_admin()

        response = self.client.get(reverse('lgr_admin_settings'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, '<h2>Settings</h2>')
        self.assertContains(response, '<label class="col-sm-2 control-label" for="id_variant_calculation_limit">'
                                      'Variant Calculation Limit</label>')
        self.assertContains(response, '<input type="number" name="variant_calculation_limit" value="100" min="2" '
                                      'class="form-control" required id="id_variant_calculation_limit">')

    def test_settings_update(self):
        self.login_admin()

        self.assertEqual(100, lgr_settings.variant_calculation_limit)
        response = self.client.post(reverse('lgr_admin_settings'), data={
            'variant_calculation_limit': 500,
            'variant_calculation_max': 5000,
            'variant_calculation_abort': 50000,
            'report_expiration_delay': 50,
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        lgr_settings.refresh_from_db()
        self.assertEqual(500, lgr_settings.variant_calculation_limit)
        self.assertEqual(5000, lgr_settings.variant_calculation_max)
        self.assertEqual(50000, lgr_settings.variant_calculation_abort)
        self.assertEqual(50, lgr_settings.report_expiration_delay)
