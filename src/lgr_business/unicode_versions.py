from django.conf import settings

from lgr_models.models import UnicodeVersion


class UnicodeVersions:

    def get(self):
        supported_versions = set(settings.SUPPORTED_UNICODE_VERSIONS).intersection(
            settings.UNICODE_DATABASES.keys())
        return UnicodeVersion.objects.filter(version__in=supported_versions)
