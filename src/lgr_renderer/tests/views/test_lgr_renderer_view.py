from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestLGRRendererView(LgrWebClientTestBase):
    def test_displays_lgr_html(self):
        self.login_admin()

        response = self.client.get('/render/html/rzlgr/1')

        self.assertTemplateUsed(response, 'lgr_renderer.html')
        self.assertContains(response, 'Label Generation Rules for the Root Zone', status_code=200)
        self.assertContains(response, '<!DOCTYPE html>')

    def test_returns_file_as_downloadable_file(self):
        self.login_admin()

        response = self.client.get('/render/html/rzlgr/1?save')

        self.assertEqual(response['Content-Disposition'], 'attachment; filename="RZ-LGR 1.html"')
