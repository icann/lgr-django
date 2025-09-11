# -*- coding: utf-8 -*-
from django.conf import settings
from munidata import UnicodeDataVersionManager


class LazyUnicodeDataVersionManager(UnicodeDataVersionManager):
    """
    This UnicodeDataVersionManager subclass registers unicode versions on demand, reading its configuration
    from the `UNICODE_DATABASES` Django setting.

    We override this by always taking the only available one
    """
    def get_db_by_version(self, unicode_version):
        try:
            return super(LazyUnicodeDataVersionManager, self).get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)
        except KeyError:
            # we won't try to catch KeyError here, instead leaving up to the caller to deal with it
            db_kwargs = settings.UNICODE_DATABASES[settings.SUPPORTED_UNICODE_VERSION]
            return manager.register(settings.SUPPORTED_UNICODE_VERSION, **db_kwargs)


# Global instance
manager = LazyUnicodeDataVersionManager()

# shortcut to facilitate import
get_db_by_version = manager.get_db_by_version
