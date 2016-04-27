# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from djangofloor.utils import FilePath, DirectoryPath

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
#                 'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient',
# 'PARSER_CLASS': 'redis.connection.HiredisParser', }, },
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
TEST_RUNNER = 'penatesserver.tests.ManagedModelTestRunner'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'cLc7rCD75uO6uFVr6ojn6AYTm2DGT2t7hb7OH5Capk29kcdy7H'

REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS': 'rest_framework.serializers.HyperlinkedModelSerializer',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'penatesserver.renderers.ListAdminRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

OPENSSL_PATH = 'openssl'
PKI_PATH = DirectoryPath('{LOCAL_PATH}/pki')
SSH_KEYGEN_PATH = 'ssh-keygen'
LDAP_BASE_DN = 'dc=test,dc=example,dc=org'

PENATES_COUNTRY = 'FR'
PENATES_ORGANIZATION = 'example.org'
PENATES_DOMAIN = 'test.example.org'
PENATES_STATE = 'Ile-de-France'
PENATES_LOCALITY = 'Paris'
PENATES_EMAIL_ADDRESS = 'admin@{PENATES_DOMAIN}'
PENATES_REALM = 'EXAMPLE.ORG'
PENATES_KEYTAB = FilePath('{PKI_PATH}/private/kadmin.keytab')
PENATES_LOCKFILE = FilePath('{PKI_PATH}/.lockfile')
PENATES_PRINCIPAL = 'penatesserver/admin@{PENATES_REALM}'
RUNNING_TESTS = False
PENATES_SUBNETS = """10.19.1.0/24,10.19.1.1
10.8.0.0/16,10.8.0.1"""

LDAP_NAME = 'ldap://192.168.56.101/'
LDAP_USER = 'cn=admin,dc=test,dc=example,dc=org'
LDAP_PASSWORD = 'toto'

PDNS_USER = 'powerdns'
PDNS_PASSWORD = 'toto'
PDNS_HOST = 'localhost'
PDNS_PORT = '5432'
PDNS_ENGINE = 'django.db.backends.sqlite3'
PDNS_NAME = FilePath('{DATA_PATH}/pdns.sqlite3')
PDNS_ADMIN_PREFIX = 'admin.'
PDNS_INFRA_PREFIX = 'infra.'

KERBEROS_IMPL = 'heimdal'  # or 'mit'
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
STORE_CLEARTEXT_PASSWORDS = False
OFFER_HOST_KEYTABS = True
DATABASE_ROUTERS = ['ldapdb.router.Router', 'penatesserver.routers.PowerdnsManagerDbRouter', ]
AUTH_USER_MODEL = 'penatesserver.DjangoUser'
KERBEROS_SERVICES = {'HTTP', 'XMPP', 'smtp', 'IPP', 'ldap', 'cifs', 'imap', 'postgres', 'host', 'afs', 'ftp',
                     'afpserver'}
DEBUG = False
AUTHENTICATION_BACKENDS = [
    'penatesserver.backends.DefaultGroupRemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
