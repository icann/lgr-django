from .default import *

# Template for deployment configuration
# Contains sensible default for production use

DEBUG = True

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

LOGGING['loggers']['lgr_web']['level'] = 'INFO'
LOGGING['loggers']['lgr_advanced']['level'] = 'INFO'
LOGGING['loggers']['lgr_auth']['level'] = 'INFO'
LOGGING['loggers']['lgr_basic']['level'] = 'INFO'
LOGGING['loggers']['lgr_idn_table_review']['level'] = 'INFO'
LOGGING['loggers']['lgr_manage']['level'] = 'INFO'
LOGGING['loggers']['lgr_renderer']['level'] = 'INFO'
LOGGING['loggers']['lgr_session']['level'] = 'INFO'
LOGGING['loggers']['lgr']['level'] = 'INFO'
LOGGING['loggers']['lgr-rule-logger']['level'] = 'INFO'
LOGGING['loggers']['celery']['level'] = 'INFO'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'storage', 'prod.db')
    }
}

#DJANGO_REDIS_CONNECTION_FACTORY = 'django_redis.pool.SentinelConnectionFactory'
#SENTINELS = [
#    ( os.environ.get('lgrSentinel1'), os.environ.get('lgrSentinelPort') ),
#    ( os.environ.get('lgrSentinel2'), os.environ.get('lgrSentinelPort') ),
#    ( os.environ.get('lgrSentinel3'), os.environ.get('lgrSentinelPort') )
#]
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": 'redis://' + os.environ.get('lgrRedisURL') + ':' + os.environ.get('lgrRedisPort')  + '/1',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

BROKER_TRANSPORT = "redis"
BROKER_HOST = os.environ.get('lgrRedisURL')
BROKER_PORT = os.environ.get('lgrRedisPort')
BROKER_VHOST = "2"

#BROKER_URL = (
#        'sentinel://:' + os.environ.get('lgrRedisPwd') + '@' + os.environ.get('lgrSentinel1') + ':' + os.environ.get('lgrSentinelPort') + '/' + os.environ.get('lgrCeleryRedisDB') + ';' +
#        'sentinel://:' + os.environ.get('lgrRedisPwd') + '@' + os.environ.get('lgrSentinel2') + ':' + os.environ.get('lgrSentinelPort') + '/' + os.environ.get('lgrCeleryRedisDB') + ';' +
#        'sentinel://:' + os.environ.get('lgrRedisPwd') + '@' + os.environ.get('lgrSentinel3') + ':' + os.environ.get('lgrSentinelPort') + '/' + os.environ.get('lgrCeleryRedisDB') )
#BROKER_TRANSPORT_OPTIONS = {
#        'master_name': os.environ.get('lgrSentinelMaster'),
#        'sentinel_kwargs': { 'password': os.environ.get('lgrRedisPwd') }
#}

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
SUPPORTED_UNICODE_VERSIONS = '14.0.0'

DEFAULT_UNICODE_VERSION = '14.0.0'

# UNICODE_DATABASES tells munidata how to instantiate the implementation of each Unicode version that we support.
# Keys are the Unicode version, like '6.3.0'
# Values are a dict of the kwargs to pass to the munidata.manager.register function along with the version.
# Currently, we assume that the underlying implementation is "picu", so the value should have the following keys:
# - icu_uc_lib: full path to the libicuuc.so file
# - icu_i18n_lib': full path to the libicui18n.so file
# - version_tag: version tag used in the function symbols in the above libraries (usually the ICU major version)
# See picu.loader.KNOWN_ICU_VERSIONS

UNICODE_DATABASES = {
    '14.0.0': {
        'icu_uc_lib': '/usr/local/lib/libicuuc.so.71',
        'icu_i18n_lib': '/usr/local/lib/libicui18n.so.71',
        'version_tag': 71,
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
