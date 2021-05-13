from .default import *

# Template for deployment configuration
# Contains sensible default for production use

DEBUG = False

# TODO: Set this list to hosts/domains served by this app
# See https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-ALLOWED_HOSTS
ALLOWED_HOSTS = [ os.environ.get('lgrURL') ]

# Uncomment if you are not using HTTPS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'storage', 'media')
TOOLS_OUTPUT_STORAGE_LOCATION = os.path.join(BASE_DIR, 'storage', 'output', 'tools')
IDN_REVIEW_USER_OUTPUT_STORAGE_LOCATION = os.path.join(BASE_DIR, 'storage', 'output', 'idn_review', 'user')
IDN_REVIEW_ICANN_OUTPUT_STORAGE_LOCATION = os.path.join(BASE_DIR, 'storage', 'output', 'idn_review', 'icann')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'storage', 'prod.db')
    }
}

DJANGO_REDIS_CONNECTION_FACTORY = 'django_redis.pool.SentinelConnectionFactory'
SENTINELS = [
    ( os.environ.get('lgrSentinel1'), os.environ.get('lgrSentinelPort') ),
    ( os.environ.get('lgrSentinel2'), os.environ.get('lgrSentinelPort') ),
    ( os.environ.get('lgrSentinel3'), os.environ.get('lgrSentinelPort') )
]
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": 'redis://' + os.environ.get('lgrSentinel1') + '/' + os.environ.get('lgrDjangoRedisDB'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.SentinelClient",
            "PASSWORD": os.environ.get('lgrRedisPwd'),
            "SERVICE_NAME": os.environ.get('lgrSentinelMaster'),
            "SENTINELS": SENTINELS,
            "SENTINEL_KWARGS": {
                'password': os.environ.get('lgrRedisPwd')
            }
        }
    }
}

BROKER_URL = (
        'sentinel://:' + os.environ.get('lgrRedisPwd') + '@' + os.environ.get('lgrSentinel1') + ':' + os.environ.get('lgrSentinelPort') + '/' + os.environ.get('lgrCeleryRedisDB') + ';' +
        'sentinel://:' + os.environ.get('lgrRedisPwd') + '@' + os.environ.get('lgrSentinel2') + ':' + os.environ.get('lgrSentinelPort') + '/' + os.environ.get('lgrCeleryRedisDB') + ';' +
        'sentinel://:' + os.environ.get('lgrRedisPwd') + '@' + os.environ.get('lgrSentinel3') + ':' + os.environ.get('lgrSentinelPort') + '/' + os.environ.get('lgrCeleryRedisDB') )
BROKER_TRANSPORT_OPTIONS = {
        'master_name': os.environ.get('lgrSentinelMaster'),
        'sentinel_kwargs': { 'password': os.environ.get('lgrRedisPwd') }
}

##### e-mail settings #####
# The host for the use of sending email (default: localhost)
#EMAIL_HOST = 'localhost'

# Port to use for the SMTP server defined above (default: 25)
#EMAIL_PORT = 25

# Username to use for the SMTP server defined in EMAIL_HOST
#EMAIL_HOST_USER

# Password to use for the SMTP server defined in EMAIL_HOST
#EMAIL_HOST_PASSWORD

# Whether to use a TLS (secure) connection when talking to the SMTP server
#EMAIL_USE_TLS = True
# Whether to use an implicit TLS (secure) connection when talking to the SMTP server
#EMAIL_USE_SSL = True

# Default email address to use (default: 'webmaster@localhost')
DEFAULT_FROM_EMAIL = os.environ.get('lgrEmail')
##### /e-mail settings #####

##### LGR Toolset Project-specific settings #####
SUPPORTED_UNICODE_VERSIONS = (
    '6.3.0',
    '6.0.0',
    '6.1.0',
    '6.2.0',
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
    '6.0.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.46',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.46',
        'version_tag': 46,
    },
    '6.1.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.49',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.49',
        'version_tag': 49,
    },
    '6.2.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.50',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.50',
        'version_tag': 50,
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

# DELETE_FROM_HERE_AFTER_GENERATION
#if SECRET_KEY == 'PLEASE GENERATE ONE':
#    import os
#    thisfile = __file__[:-1] if __file__.endswith('pyc') else __file__
#    path = os.path.join(os.path.dirname(thisfile), '..', '..', '..', 'bin', 'gen_secret_key')
#    exec(open(path).read())
#    secret_key = write_secret_key(thisfile) # overwrite me
#    SECRET_KEY = secret_key
# DELETE_TO_HERE_AFTER_GENERATION
SECRET_KEY = os.environ.get('lgrSecretKey')
