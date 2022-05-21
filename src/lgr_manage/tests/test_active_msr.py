from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class MyTestCase(LgrWebClientTestBase):
    def test_update_active_when_logged_in(self):
        self.login()

        self.assertEqual(True, False)