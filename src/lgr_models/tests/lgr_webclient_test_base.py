from django.test import TestCase

from lgr_auth.models import LgrRole, LgrUser


class LgrWebClientTestBase(TestCase):
    active_root_zones = ['RZ-LGR 5']
    active_idna_repertoire = ['idna2008_10.0.0']
    active_msr = ['msr-4-wle-rules-25jan19-en']
    default_root_zones = ['RZ-LGR 1', 'RZ-LGR 2', 'RZ-LGR 3', 'RZ-LGR 4', 'RZ-LGR 5']

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
        try:
            user = LgrUser.objects.get(email='test-admin@lgr.example')
        except LgrUser.DoesNotExist:
            user = LgrUser.objects.create_superuser('test-admin@lgr.example', '1234')
        self.assertTrue(self.client.login(username=user.email, password='1234'))
        return user
