from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestLGRToolAdmin(LgrWebClientTestBase):
    def test_renders_tabs(self):
        self.login_admin()

        response = self.client.get('/m/')

        self.assertContains(response, '<a href="/m/rz-lgr">Root Zone LGRs</a>', status_code=200)
        self.assertContains(response, '<a href="/m/ref-lgr">Reference LGRs</a>')
        self.assertContains(response, '<a href="/m/msr">MSR</a>')
        self.assertContains(response, '<a href="/m/idna">IDNA Repertoires</a>')
        self.assertContains(response, '<a href="/m/users">User management</a>')
        self.assertContains(response, '<a href="/m/settings">Tool Setting</a>')
