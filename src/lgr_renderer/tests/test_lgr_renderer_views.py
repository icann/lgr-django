from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestLgrRendererView(LgrWebClientTestBase):
    def test_display_lgr_html(self):
        self.login_admin()
        response = self.client.get('/render/html/rzlgr/1')
        self.assertContains(response, 'Label Generation Rules for the Root Zone', status_code=200)
        self.assertContains(response, '<!DOCTYPE html>')
