from django.test import TestCase

from lgr_auth.models import LgrUser, LgrRole


class LgrWebClientTestBase(TestCase):
    active_root_zones = ['RZ-LGR 5']
    active_msr = ['msr-4-wle-rules-25jan19-en']
    default_root_zones = ['RZ-LGR 1', 'RZ-LGR 2', 'RZ-LGR 3', 'RZ-LGR 4', 'RZ-LGR 5']

    def setUp(self):
        """
        Verify if unit tests are properly configured. If you get "'module' object has no attribute 'ROOT_URLCONF'"
        error here, please go to Settings > Languages & Frameworks > Django and set your setting file
        """
        response = self.client.get('/')
        self.assertContains(response, 'Welcome to the LGR (Label Generation Ruleset) Tools')

    def login_user(self):
        user = LgrUser.objects.create_user(email='test-user@lgr.example', password='1234', role=LgrRole.USER.value)
        is_logged_in = self.client.login(username=user.email, password='1234')
        self.assertTrue(is_logged_in)
        return user

    def login_icann(self):
        user = LgrUser.objects.create_user(email='test-icann@lgr.example', password='1234', role=LgrRole.ICANN.value)
        is_logged_in = self.client.login(username=user.email, password='1234')
        self.assertTrue(is_logged_in)
        return user

    def login_admin(self):
        user = LgrUser.objects.create_superuser('test-admin@lgr.example', '1234')
        is_logged_in = self.client.login(username=user.email, password='1234')
        self.assertTrue(is_logged_in)
        return user
