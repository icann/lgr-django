from .default import *

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

LOGGING['loggers']['lgr_web']['level'] = 'DEBUG'
LOGGING['loggers']['lgr_advanced']['level'] = 'DEBUG'
LOGGING['loggers']['lgr_auth']['level'] = 'DEBUG'
LOGGING['loggers']['lgr_basic']['level'] = 'DEBUG'
LOGGING['loggers']['lgr_idn_table_review']['level'] = 'DEBUG'
LOGGING['loggers']['lgr_manage']['level'] = 'DEBUG'
LOGGING['loggers']['lgr_renderer']['level'] = 'DEBUG'
LOGGING['loggers']['lgr_session']['level'] = 'DEBUG'
LOGGING['loggers']['lgr']['level'] = 'DEBUG'
LOGGING['loggers']['lgr-rule-logger']['level'] = 'DEBUG'
LOGGING['loggers']['celery']['level'] = 'DEBUG'

METADATA_UNICODE_VERSIONS = (
    '15.1.0',
)
SUPPORTED_UNICODE_VERSION = '15.1.0'
DEFAULT_UNICODE_VERSION = '15.1.0'

UNICODE_DATABASES = {
    '15.1.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.74',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.74',
        'version_tag': 74,
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR + '/dev.db'
    }
}
SECRET_KEY = 'TestOnly'
