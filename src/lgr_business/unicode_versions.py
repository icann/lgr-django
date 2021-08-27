from django.conf import settings
from django.db.models import QuerySet

from lgr_models.models import UnicodeVersion


class UnicodeVersions:

    def get(self) -> QuerySet[UnicodeVersion]:
        supported_versions = set(settings.SUPPORTED_UNICODE_VERSIONS).intersection(
            settings.UNICODE_DATABASES.keys())
        return UnicodeVersion.objects.filter(version__in=supported_versions)

    def get_activated(self) -> QuerySet[UnicodeVersion]:
        return self.get().filter(activated=True)
