import unittest

from lgr_models.models.unicode import UnicodeVersion
from lgr_models.tests.test_unicode_version import TestUnicodeVersion


class TestUnicodeVersions(TestUnicodeVersion):

    @unittest.skip('Disabled for now')
    def test_unicode_tab(self):
        self.login_admin()

        response = self.client.get('/m/unicode-versions')
        self.assertContains(response, f'<td>{self.a_version_supported}</td>', status_code=200)
        # check that all unicode versions are unactivated by default, and that the hidden input is the reverse: True:
        self.assertContains(response, '<input type="hidden" name="activated" value="True">')

    @unittest.skip('Disabled for now')
    def test_unicode_edit(self):
        self.login_admin()

        self.assertEqual(self.a_unicode_version.activated, False)
        self.client.post(f'/m/unicode-versions/{self.a_unicode_version.pk}/update', {'activated': True})
        new_unicode_version = UnicodeVersion.objects.get(version=self.a_version_supported)
        self.assertEqual(new_unicode_version.activated, True)
        self.assertListEqual([new_unicode_version], list(UnicodeVersion.get_activated()))

    @unittest.skip('Disabled for now')
    def test_unicode_create(self):
        self.login_admin()

        initial_versions = list(UnicodeVersion.objects.all().values_list('version', flat=True))

        new_version = '9.9.9-test'
        self.assertIn('10.0.0', initial_versions)
        self.assertNotIn(new_version, initial_versions)

        response = self.client.post('/m/unicode-versions/create', {'version': new_version}, follow=True)
        self.assertEqual(response.status_code, 200)
        new_versions = list(UnicodeVersion.objects.all().values_list('version', flat=True))
        self.assertIn(new_version, new_versions)

        new_version = UnicodeVersion.objects.get(version=new_version)
        self.assertEqual(new_version.activated, False)
