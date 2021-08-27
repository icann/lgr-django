from django.test import TestCase

from lgr_models.models import UnicodeVersion
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_web import settings


class TestUnicodeVersion(LgrWebClientTestBase):

    def setUp(self):
        self.versions_supported = set(settings.SUPPORTED_UNICODE_VERSIONS).intersection(
            settings.UNICODE_DATABASES.keys())
        # this test require that at least one version of unicode is supported:
        self.a_version_supported = set(self.versions_supported).pop()
        self.a_unicode_version = UnicodeVersion.objects.get(version=self.a_version_supported)

    def test_unicode_version(self):
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
