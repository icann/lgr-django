from tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestLgrRendererDbView(LgrWebClientTestBase):
    html = '<!DOCTYPE html>'

    def setUp(self):
        self.login()

    def test_display_lgr_from_db_html(self):
        response = self.client.get('/a/render/html/1')
        self.assertContains(response, self.root_zone_label, status_code=200)
        self.assertContains(response, self.html)

    def test_display_lgr_from_db_xml(self):
        response = self.client.get('/a/render/xml/1')
        self.assertContains(response, self.root_zone_label, status_code=200)
        self.assertNotContains(response, self.html)

    def test_display_lgr_from_db_wrong_format(self):
        response = self.client.get('/a/render/wrong-format/1')
        self.assertEqual(response.status_code, 404)
