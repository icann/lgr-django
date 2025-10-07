from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestLGRDisplayView(LgrWebClientTestBase):
    def test_displays_file(self):
        self.login_admin()

        response = self.client.get('/render/file/rzlgr/1')

        self.assertEqual(response['Content-Type'], 'text/xml')
        self.assertContains(response, 'Label Generation Rules for the Root Zone', status_code=200)

    def test_returns_file_as_downloadable_file(self):
        self.login_admin()

        response = self.client.get('/render/dl/rzlgr/1')

        # TODO: We need proper teardowns on tests when files being added to achieve repeatable results
        self.assertIn('attachment; filename=', response['Content-Disposition'])
