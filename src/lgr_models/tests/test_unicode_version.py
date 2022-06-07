import unittest

from django.conf import settings
from django.test import override_settings

from lgr_models.models.unicode import UnicodeVersion
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestUnicodeVersion(LgrWebClientTestBase):

    def setUp(self):
        self.versions_supported = set(settings.SUPPORTED_UNICODE_VERSIONS).intersection(
            settings.UNICODE_DATABASES.keys())
        # this test requires that at least one version of unicode is supported:
        self.a_version_supported = set(self.versions_supported).pop()
        self.a_unicode_version = UnicodeVersion.objects.get(version=self.a_version_supported)


class TestUnicodeVersionModel(TestUnicodeVersion):

    @override_settings(DEFAULT_UNICODE_VERSION='10.0.0',
                       SUPPORTED_UNICODE_VERSIONS=('6.3.0', '10.0.0'),
                       UNICODE_DATABASES={'6.3.0': {}, '10.0.0': {}})
    def test_default_version(self):
        self.assertEqual(settings.DEFAULT_UNICODE_VERSION, '10.0.0')
        default_version = UnicodeVersion.default()
        self.assertEqual(default_version.version, '10.0.0')

    @override_settings(DEFAULT_UNICODE_VERSION='10.0.0',
                       SUPPORTED_UNICODE_VERSIONS=('6.3.0', '10.0.0'),
                       UNICODE_DATABASES={'6.3.0': {}, '10.0.0': {}})
    def test_no_default_version(self):
        """
        Return the first element of the list when no default unicode version is specified
        """
        del settings.DEFAULT_UNICODE_VERSION
        default_version = UnicodeVersion.default()
        self.assertEqual(default_version.version, '6.3.0')

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
            '10.0.0',
            '11.0.0',
            '12.0.0',
            '13.0.0',
            '14.0.0'
        })
