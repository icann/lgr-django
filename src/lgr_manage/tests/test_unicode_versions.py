from lgr_models.models import UnicodeVersion
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestUnicodeVersion(LgrWebClientTestBase):
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
        self.assertContains(response, '<td>10.0.0</td>', status_code=200)
        self.assertContains(response, '/unicode-version/1')

    def test_unicode_edit(self):
        self.login()

        response = self.client.get('/m/unicode-version/1')
        self.assertContains(response, '6.0.0', status_code=200)
        unicode_version_6 = UnicodeVersion.objects.get(version='6.0.0')
        self.assertEqual(unicode_version_6.activated, False)
        self.client.post('/m/unicode-version/1', {'activated': 'on'})
        unicode_version_6 = UnicodeVersion.objects.get(version='6.0.0')
        self.assertEqual(unicode_version_6.activated, True)
