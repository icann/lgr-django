from lgr_business.unicode_versions import UnicodeVersions
from lgr_models.models import UnicodeVersion
from lgr_models.tests.test_unicode_version import TestUnicodeVersion


class TestUnicodeVersions(TestUnicodeVersion):

    def test_manage_tabs(self):
        self.login()

        response = self.client.get('/m/')
        self.assertContains(response, '<a href="/m/rz-lgr">Root Zone LGRs</a>', status_code=200)
        self.assertContains(response, '<a href="/m/ref-lgr">Reference LGRs</a>')
        self.assertContains(response, '<a href="/m/users">User management</a>')
        self.assertContains(response, '<a href="/m/unicode-versions">Unicode Versions</a>')

    def test_unicode_tab(self):
        self.login()

        response = self.client.get('/m/unicode-versions')
        self.assertContains(response, f'<td>{self.a_version_supported}</td>', status_code=200)
        # check that all unicode versions are unactivated by default, and that the hidden input is the reverse: True:
        self.assertContains(response, """<input type="hidden" name="activated" value="True">""")

    def test_unicode_edit(self):
        self.login()

        self.assertEqual(self.a_unicode_version.activated, False)
        self.client.post(f'/m/unicode-versions/{self.a_unicode_version.pk}/update', {'activated': True})
        new_unicode_version = UnicodeVersion.objects.get(version=self.a_version_supported)
        self.assertEqual(new_unicode_version.activated, True)
        self.assertListEqual([new_unicode_version], list(UnicodeVersions().get_activated()))
