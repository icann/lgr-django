from django.test import SimpleTestCase


class TestLGRModesView(SimpleTestCase):
    def test_renders_home_page_without_login(self):
        response = self.client.get('/')

        self.assertTemplateUsed(response, 'lgr_modes.html')
        self.assertContains(response, 'Welcome to the LGR (Label Generation Ruleset) Tools')
