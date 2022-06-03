from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestAdmin(LgrWebClientTestBase):

    def test_manage_tabs(self):
        self.login_admin()

        response = self.client.get('/m/')
        self.assertContains(response, '<a href="/m/rz-lgr">Root Zone LGRs</a>', status_code=200)
        self.assertContains(response, '<a href="/m/ref-lgr">Reference LGRs</a>')
        self.assertContains(response, '<a href="/m/users">User management</a>')
        # FIXME: disable for now
        # self.assertContains(response, '<a href="/m/unicode-versions">Unicode Versions</a>')
