from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class MyTestCase(LgrWebClientTestBase):
    def test_update_active_when_logged_in(self):
        self.login()

        response = self.client.get('/m/msr')
        self.assertContains(response, '<a href="/m/rz-lgr">Root Zone LGRs</a>', status_code=200)
