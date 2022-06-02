from django.test import TestCase

from lgr_auth.models import LgrUser


class LgrWebClientTestBase(TestCase):
    default_root_zones = ['RZ-LGR 1', 'RZ-LGR 2', 'RZ-LGR 3', 'RZ-LGR 4', 'RZ-LGR 5']
    default_msr = ['IDNA2008 10.0.0',
                   'IDNA2008 5.2.0',
                   'IDNA2008 6.0.0',
                   'IDNA2008 6.1.0',
                   'IDNA2008 6.2.0',
                   'IDNA2008 6.3.0',
                   'IDNA2008 7.0.0',
                   'IDNA2008 8.0.0',
                   'IDNA2008 9.0.0',
                   'MSR 2',
                   'MSR 3',
                   'MSR 4']

    def setUp(self):
        """
        Verify if unit tests are properly configured. If you get "'module' object has no attribute 'ROOT_URLCONF'"
        error here, please go to Settings > Languages & Frameworks > Django and set your setting file
        """
        response = self.client.get('/')
        self.assertContains(response, 'Welcome to the LGR (Label Generation Ruleset) Tools')

    def login_admin(self):
        user = LgrUser.objects.create_superuser('test-admin@lgr.example', '1234')
        is_logged_in = self.client.login(username=user.email, password='1234')
        self.assertTrue(is_logged_in)
        return user
