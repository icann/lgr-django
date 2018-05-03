from .default import *
import sys

# Copy Me To local.py Please

# Template for deployment configuration
# Contains sensible default for production use

DEBUG = False

# TODO: Set this list to hosts/domains served by this app
# See https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-ALLOWED_HOSTS
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
ALLOWED_HOSTS = ['*']

#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR + '/lgr-sqlite3.db',
    }
}

# Configure file handler to output logs to specific file location
LOGGING['handlers']['file'] = {'level': 'DEBUG', 'class': 'logging.FileHandler', 'filename': '/var/log/lgr/lgr-django.log', 'formatter': 'default'}

# Set handler for modules
for mod in ['django.request', 'lgr_web', 'lgr_editor', 'lgr']:
	    LOGGING['loggers'][mod]['handlers'] += ['file']

##### LGR Toolset Project-specific settings #####
# Where the XML files are stored on the filesystem
# For the repertoires
REPERTOIRE_STORAGE_LOCATION = os.path.join(BASE_DIR, 'resources', 'repertoires')

# For the built-in LGRs
LGR_STORAGE_LOCATION = os.path.join(BASE_DIR, 'resources', 'lgr')

# Filepath of the LGR RNG schema file
LGR_RNG_FILE = os.path.join(BASE_DIR, 'resources', 'lgr.rng')

# Default variant type when creating new variant
DEFAULT_VARIANT_TYPE = "block"

SUPPORTED_UNICODE_VERSIONS = (
    '6.3.0',
    '7.0.0',
    '8.0.0',
    '9.0.0',
    '10.0.0'
)

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
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.52',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.52',
        'version_tag': 52,
    },
    '7.0.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.54',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.54',
        'version_tag': 54,
    },
    '8.0.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.56',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.56',
        'version_tag': 56,
    },
    '9.0.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.58',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.58',
        'version_tag': 58,
    },
    '10.0.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.60',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.60',
        'version_tag': 60,
    }
}
##### /LGR Toolset Project-specific settings #####

SECRET_KEY = '__this__is__not__secret__7aqt8aUQvmheBnUewTYF37ZtPVuBsKBTuE5hA'
DEFAULT_FROM_EMAIL = "postmaster@example.com"
EMAIL_HOST = "localhost"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# 1.8.1 celery now uses redis
BROKER_URL = 'redis://:oce-6EA-zd2@localhost:6379/7'
# in a subdir
FORCE_SCRIPT_NAME = '/lgr'
