# -*- coding: utf-8 -*-
from __future__ import unicode_literals
__author__ = 'flanker'

########################################################################################################################
# sessions
########################################################################################################################
SESSION_REDIS_PREFIX = 'session'
SESSION_REDIS_HOST = '{REDIS_HOST}'
SESSION_REDIS_PORT = '{REDIS_PORT}'
SESSION_REDIS_DB = 10


########################################################################################################################
# caching
########################################################################################################################
# CACHES = {
#     'default': {'BACKEND': 'django_redis.cache.RedisCache', 'LOCATION': 'redis://{REDIS_HOST}:{REDIS_PORT}/11',
#                 'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient', 'PARSER_CLASS': 'redis.connection.HiredisParser', }, },
#     }

########################################################################################################################
# django-redis-websocket
########################################################################################################################

########################################################################################################################
# celery
########################################################################################################################

FLOOR_INSTALLED_APPS = ['penatesserver', 'rest_framework', ]
FLOOR_INDEX = 'penatesserver.views.index'
FLOOR_URL_CONF = 'penatesserver.root_urls.urls'
FLOOR_PROJECT_NAME = 'Penates Server'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'cLc7rCD75uO6uFVr6ojn6AYTm2DGT2t7hb7OH5Capk29kcdy7H'


REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS': 'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

OPENSSL_PATH = 'openssl'
PKI_PATH = '{LOCAL_PATH}/pki'

LDAP_BASE_DN = 'dc=test,dc=example,dc=org'
PENATES_DOMAIN = 'test.example.org'
PENATES_COUNTRY = 'FR'
PENATES_ORGANIZATION = 'example.org'
PENATES_STATE = 'Île-de-France'
PENATES_LOCALITY = 'Paris'
PENATES_EMAIL_ADDRESS = 'admin@test.example.org'

DATABASES = {
    'default': {
        'ENGINE': '{DATABASE_ENGINE}',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '{DATABASE_NAME}',  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '{DATABASE_USER}',
        'PASSWORD': '{DATABASE_PASSWORD}',
        'HOST': '{DATABASE_HOST}',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '{DATABASE_PORT}',  # Set to empty string for default.
    },
    'ldap': {
        'ENGINE': 'ldapdb.backends.ldap',
        'NAME': 'ldap://192.168.56.101/',
        'USER': 'cn=admin,dc=test,dc=example,dc=org',
        'PASSWORD': 'toto',
    }
}
DATABASE_ROUTERS = ['ldapdb.router.Router']
