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

FLOOR_INSTALLED_APPS = ['penatesserver', 'rest_framework', 'penatesserver.powerdns', ]
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
        'rest_framework.permissions.AllowAny',
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}


OPENSSL_PATH = 'openssl'
PKI_PATH = '{LOCAL_PATH}/pki'
SSH_KEYGEN_PATH = 'ssh-keygen'
LDAP_BASE_DN = 'dc=test,dc=example,dc=org'

PENATES_COUNTRY = 'FR'
PENATES_ORGANIZATION = 'example.org'
PENATES_DOMAIN = 'test.example.org'
PENATES_STATE = 'Île-de-France'
PENATES_LOCALITY = 'Paris'
PENATES_EMAIL_ADDRESS = 'admin@{PENATES_DOMAIN}'
PENATES_REALM = 'EXAMPLE.ORG'
PENATES_KEYTAB = '{LOCAL_PATH}/pki/private/kadmin.keytab'
PENATES_PRINCIPAL = 'penatesserver/admin@{PENATES_REALM}'
PENATES_ROUTER = '192.168.56.1'
PENATES_SUBNET = '192.168.56.0/24'


LDAP_NAME = 'ldap://192.168.56.101/'
LDAP_USER = 'cn=admin,dc=test,dc=example,dc=org'
LDAP_PASSWORD = 'toto'

PDNS_ENGINE = 'django.db.backends.postgresql_psycopg2'
PDNS_NAME = 'powerdns'
PDNS_USER = 'powerdns'
PDNS_PASSWORD = 'toto'
PDNS_HOST = 'localhost'
PDNS_PORT = '5432'

DATABASES = {
    'default': {
        'ENGINE': '{DATABASE_ENGINE}',
        'NAME': '{DATABASE_NAME}',
        'USER': '{DATABASE_USER}',
        'PASSWORD': '{DATABASE_PASSWORD}',
        'HOST': '{DATABASE_HOST}',
        'PORT': '{DATABASE_PORT}',
    },
    'ldap': {
        'ENGINE': 'ldapdb.backends.ldap',
        'NAME': '{LDAP_NAME}',
        'USER': '{LDAP_USER}',
        'PASSWORD': '{LDAP_PASSWORD}',
    },
    'powerdns': {
        'ENGINE': '{PDNS_ENGINE}',
        'NAME': '{PDNS_NAME}',
        'USER': '{PDNS_USER}',
        'PASSWORD': '{PDNS_PASSWORD}',
        'HOST': '{PDNS_HOST}',
        'PORT': '{PDNS_PORT}',
    },

}
DATABASE_ROUTERS = ['ldapdb.router.Router', 'penatesserver.routers.PowerdnsManagerDbRouter', ]
AUTH_USER_MODEL = 'penatesserver.DjangoUser'

DEBUG = True
