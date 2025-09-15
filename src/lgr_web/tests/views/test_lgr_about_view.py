from django.conf import settings
from django.test import SimpleTestCase


class TestLGRAboutView(SimpleTestCase):
    def test_renders_about_page_without_login(self):
        response = self.client.get('/about/')

        self.assertTemplateUsed(response, 'about.html')
        self.assertContains(response, 'Supported Unicode version:')
        self.assertIn('output', response.context_data)
        self.assertEqual(response.context_data['output'], settings.SUPPORTED_UNICODE_VERSION)
