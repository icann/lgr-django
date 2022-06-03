from django.urls import reverse

from lgr_models.tests.test_unicode_version import TestUnicodeVersion
from lgr_web.config import lgr_settings


class TestUnicodeVersions(TestUnicodeVersion):

    def test_settings_user_unauthorized(self):
        self.login_user()

        response = self.client.get(reverse('lgr_admin_settings'))
        self.assertEqual(response.status_code, 403)

    def test_settings_icann_unauthorized(self):
        self.login_icann()

        response = self.client.get(reverse('lgr_admin_settings'))
        self.assertEqual(response.status_code, 403)

    def test_settings_tab(self):
        self.login_admin()

        response = self.client.get(reverse('lgr_admin_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2>Settings</h2>')
        self.assertContains(response, '<label class="col-sm-2 control-label" for="id_variant_calculation_limit">'
                                      'Variant Calculation Limit</label>')
        self.assertContains(response, '<input type="number" name="variant_calculation_limit" value="1000" min="2" '
                                      'class="form-control" required id="id_variant_calculation_limit">')

    def test_settings_update(self):
        self.login_admin()

        self.assertEqual(1000, lgr_settings.variant_calculation_limit)
        self.client.post(reverse('lgr_admin_settings'), data={'variant_calculation_limit': 500})
        lgr_settings.refresh_from_db()
        self.assertEqual(500, lgr_settings.variant_calculation_limit)
