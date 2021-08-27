from django.test import TestCase, override_settings

from lgr_models.models import UnicodeVersion


class TestUnicodeVersions(TestCase):

    def test_unicode_versions(self):
        qs = UnicodeVersion.objects.all()
        unicode_versions = set(qs.values_list('version', flat=True))
        self.assertSetEqual(unicode_versions, {
            '6.3.0',
            '6.0.0',
            '6.1.0',
            '6.2.0',
            '7.0.0',
            '8.0.0',
            '9.0.0',
            '10.0.0'
        })
