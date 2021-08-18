from django.test import TestCase

from lgr_auth.models import LgrUser


class LgrWebClientTestBase(TestCase):
    root_zone_label = 'Label Generation Rules for the Root Zone'

    def setUp(self):
        """
        Verify if unit tests are properly configured. If you get "'module' object has no attribute 'ROOT_URLCONF'"
        error here, please go to Settings > Languages & Frameworks > Django and set your setting file
        """
        response = self.client.get('/')
        self.assertContains(response, 'Welcome to the LGR (Label Generation Ruleset) Tools')

    def login(self):
        user = LgrUser.objects.create_superuser('test@lgr.example', '1234')
        is_logged_in = self.client.login(username=user.email, password='1234')
        self.assertTrue(is_logged_in)
