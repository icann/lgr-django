from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestLgrRendererDbView(LgrWebClientTestBase):
    def test_display_lgr_from_db_html(self):
        self.login()
        response = self.client.get('/a/render/1')
        self.assertContains(response, 'Label Generation Rules for the Root Zone', status_code=200)
        self.assertContains(response, '<!DOCTYPE html>')
