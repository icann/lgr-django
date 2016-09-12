# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from munidata import UnicodeDataVersionManager


class LazyUnicodeDataVersionManager(UnicodeDataVersionManager):
    """
    This UnicodeDataVersionManager subclass registers unicode versions on demand, reading its configuration
    from the `UNICODE_DATABASES` Django setting.
    """
    def get_db_by_version(self, unicode_version):
        try:
            return super(LazyUnicodeDataVersionManager, self).get_db_by_version(unicode_version)
        except KeyError:
            # we won't try to catch KeyError here, instead leaving up to the caller to deal with it
            db_kwargs = settings.UNICODE_DATABASES[unicode_version]
            return manager.register(unicode_version, **db_kwargs)


# Global instance
manager = LazyUnicodeDataVersionManager()

# shortcut to facilitate use as `settings.UNIDB_LOADER_FUNC`
get_db_by_version = manager.get_db_by_version
