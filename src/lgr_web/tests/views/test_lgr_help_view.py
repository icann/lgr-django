from django.test import SimpleTestCase


class TestLGRHelpView(SimpleTestCase):
    def test_renders_help_page_without_login(self):
        response = self.client.get('/help/')

        self.assertTemplateUsed(response, 'help.html')
        self.assertContains(response, 'For more information about the LGR Toolset')
