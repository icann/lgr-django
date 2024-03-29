"""
Django settings for lgr_web project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

from django.utils.translation import ugettext_lazy as _
from kombu import Queue


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'PLEASE GENERATE ONE'

DEBUG = False

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'dal',
    'dal_select2',
    'django.contrib.admin',  # XXX needed by django-autocomplete-light 3.8.2 (see https://github.com/yourlabs/django-autocomplete-light/issues/1195#issuecomment-905648958)
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'django_celery_results',
    'lgr_models',
    'lgr_session',
    'lgr_auth',
    'lgr_tasks',
    'lgr_advanced',
    'lgr_advanced.lgr_editor',
    'lgr_advanced.lgr_validator',
    'lgr_advanced.lgr_tools',
    'lgr_basic',
    'lgr_idn_table_review',
    'lgr_idn_table_review.icann_tools',
    'lgr_idn_table_review.idn_tool',
    'lgr_manage',
    'lgr_renderer',
    'lgr_utils',
    'widget_tweaks',
    'django_cleanup.apps.CleanupConfig',  # should be placed last
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'lgr_advanced.lgr_tools.middleware.UnicodeDecodeErrorMiddleWare',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'  # for iframes containing popups

# Custom auth user model
AUTH_USER_MODEL = 'lgr_auth.LgrUser'

AUTHENTICATION_BACKENDS = (
    # 'lgr_auth.backend.JWTBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# The authentication method among:
#   - Django: Basic authentication with Django
#   - ICANN: SSO with ICANN
AUTH_METHOD = 'Django'


# Redirect URL after auth
LOGIN_REDIRECT_URL = 'lgr_home'
# Default LOGIN URL (use named URLs)
LOGIN_URL = 'login'
# Redirect URL after logout
LOGOUT_REDIRECT_URL = 'lgr_home'

ROOT_URLCONF = 'lgr_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lgr_web.wsgi.application'

# See http://docs.djangoproject.com/en/dev/topics/logging and
# http://docs.python.org/2/library/logging.config.html#configuration-dictionary-schema
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(name)s [%(funcName)s:%(lineno)d] %(message)s'
        },
        'simple': {
            'format': '%(levelname)s [%(funcName)s:%(lineno)d] %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'console_rule_logger': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'lgr_web': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_auth': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_advanced': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_advanced.lgr_editor': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_advanced.lgr_tools': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_advanced.lgr_validator': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_basic': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_idn_table_review': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_manage': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_renderer': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr_session': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'lgr': {
             'handlers': ['console'],
             'level': 'ERROR',
         },
        'lgr-rule-logger': {
            'handlers': ['console_rule_logger'],
            'level': 'INFO'  # Need to be set to INFO!
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

# where the non-app gettext translation catalogues can be found
LOCALE_PATHS = (
    os.path.abspath(os.path.join(BASE_DIR, 'locale')),
)

LANGUAGES = (
    ('ar', _('Arabic')),
    ('en', _('English')),
    ('fr', _('French')),
)

TIME_ZONE = 'UTC'
USE_TZ = True

# Session
# https://docs.djangoproject.com/en/1.8/topics/http/sessions/
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True    # Secure setting - turn off for development
CSRF_COOKIE_HTTPONLY = False  # CSRF cookie is used by some JS for reference editing
CSRF_COOKIE_SECURE = True  # Secure setting for CSRF cookie - turn off for development

# How long to set the Session cookie for
SESSION_COOKIE_AGE = 60*60*24*7  # 1 week

# Where to store session data - use the cached database:
# Read from memory, write to DB
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Cache
# https://docs.djangoproject.com/fr/1.8/topics/cache/
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        # DB 0 is used for Celery broker
        'LOCATION': 'redis://localhost:6379/1',
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(os.path.join(BASE_DIR, 'assets')),
)

# User uploaded files
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


##### LGR Toolset Project-specific settings #####
# Where the XML files are stored on the filesystem
# For the repertoires
REPERTOIRE_STORAGE_LOCATION = os.path.join(BASE_DIR, 'resources', 'repertoires')

# For the built-in LGRs
LGR_STORAGE_LOCATION = os.path.join(BASE_DIR, 'resources', 'lgr')

# Filepath of the LGR RNG schema file
LGR_RNG_FILE = os.path.join(BASE_DIR, 'resources', 'lgr.rng')

MAX_USER_IDN_REVIEW_INPUT = 20

# Duration in second for which the tools output files are stored
STORAGE_DURATION = 60*60*24*7  # 1 week

# Default variant type when creating new variant
DEFAULT_VARIANT_TYPE = "blocked"

SUPPORTED_UNICODE_VERSION = '6.3.0'
METADATA_UNICODE_VERSIONS = (
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
    '12.0.0',
    '14.0.0',
)

# ICANN TLDs URL
ICANN_TLDS = 'http://data.iana.org/TLD/tlds-alpha-by-domain.txt'

# UNICODE_DATABASES tells munidata how to instantiate the implementation of each Unicode version that we support.
# Keys are the Unicode version, like '6.3.0'
# Values are a dict of the kwargs to pass to the munidata.manager.register function along with the version.
# Currently, we assume that the underlying implementation is "picu", so the value should have the following keys:
# - icu_uc_lib: full path to the libicuuc.so file
# - icu_i18n_lib': full path to the libicui18n.so file
# - version_tag: version tag used in the function symbols in the above libraries (usually the ICU major version)
# See picu.loader.KNOWN_ICU_VERSIONS

UNICODE_DATABASES = {
    '6.3.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.52.1',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.52.1',
        'version_tag': 52,
    },
}

# default unicode version in dropdowns across the application
DEFAULT_UNICODE_VERSION = '6.3.0'

# A list of IDN tables to handle in ICANN IDN table review. None for all.
ICANN_IDN_REVIEW_TABLES = []


##### Celery configuration parameters #####

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CELERYD_HIJACK_ROOT_LOGGER = False

CELERYD_TASK_SOFT_TIME_LIMIT = 60*60*24  # 24h
CELERYD_TASK_TIME_LIMIT = 3600*25  # 25h
# CELERY_ALWAYS_EAGER = True  # set to True to skip using queues

CELERY_QUEUES = (
    Queue('celery', routing_key='transient',
          delivery_mode=1),
)

BROKER_URL = 'redis://localhost:6379/0'

# Django Celery Results configuration
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

# Periodic tasks
TASK_REFRESH_FREQUENCY = 3600 * 24
CELERYBEAT_SCHEDULE = {
    "calculate_index_variant_labels_tlds": {
        "task": "lgr_tasks.tasks.calculate_index_variant_labels_tlds",
        "schedule": TASK_REFRESH_FREQUENCY,
        'options': {
            'expires': 3600 * 10,
        }
    },
    "clean_reports": {
        "task": "lgr_tasks.tasks.clean_reports",
        "schedule": TASK_REFRESH_FREQUENCY,
        'options': {
            'expires': 3600 * 10,
        }
    },
}
CELERYBEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

##### /Celery configuration parameters #####
