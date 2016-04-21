# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from djangofloor.iniconf import OptionParser, bool_setting, strip_split

__author__ = 'Matthieu Gallet'
# noinspection PyTypeChecker
INI_MAPPING = [

    OptionParser('DATABASE_ENGINE', 'database.engine'),
    OptionParser('DATABASE_NAME', 'database.name'),
    OptionParser('DATABASE_USER', 'database.user'),
    OptionParser('DATABASE_PASSWORD', 'database.password'),
    OptionParser('DATABASE_HOST', 'database.host'),
    OptionParser('DATABASE_PORT', 'database.port'),

    OptionParser('PDNS_ENGINE', 'powerdns.engine'),
    OptionParser('PDNS_NAME', 'powerdns.name'),
    OptionParser('PDNS_USER', 'powerdns.user'),
    OptionParser('PDNS_PASSWORD', 'powerdns.password'),
    OptionParser('PDNS_HOST', 'powerdns.host'),
    OptionParser('PDNS_PORT', 'powerdns.port'),

    OptionParser('LDAP_BASE_DN', 'ldap.base_dn'),
    OptionParser('LDAP_NAME', 'ldap.name'),
    OptionParser('LDAP_USER', 'ldap.user'),
    OptionParser('LDAP_PASSWORD', 'ldap.password'),

    OptionParser('PENATES_DOMAIN', 'penates.domain'),
    OptionParser('PENATES_COUNTRY', 'penates.country'),
    OptionParser('PENATES_REALM', 'penates.realm'),
    OptionParser('PENATES_ORGANIZATION', 'penates.organization'),
    OptionParser('PENATES_STATE', 'penates.state'),
    OptionParser('PENATES_LOCALITY', 'penates.locality'),
    OptionParser('PENATES_EMAIL_ADDRESS', 'penates.email_address'),
    OptionParser('PENATES_SUBNETS', 'penates.subnets'),

    OptionParser('SERVER_NAME', 'global.server_name'),
    OptionParser('PENATES_KEYTAB', 'global.keytab'),
    OptionParser('KERBEROS_SERVICES', 'global.kerberos_services', converter=strip_split),
    OptionParser('PROTOCOL', 'global.protocol'),
    OptionParser('BIND_ADDRESS', 'global.bind_address'),
    OptionParser('LOCAL_PATH', 'global.data_path'),
    OptionParser('ADMIN_EMAIL', 'global.admin_email'),
    OptionParser('TIME_ZONE', 'global.time_zone'),
    OptionParser('LANGUAGE_CODE', 'global.language_code'),
    OptionParser('OFFER_HOST_KEYTABS', 'global.offer_host_keytabs'),
    OptionParser('FLOOR_AUTHENTICATION_HEADER', 'global.remote_user_header'),
    OptionParser('SECRET_KEY', 'global.secret_key'),
    OptionParser('FLOOR_DEFAULT_GROUP_NAME', 'global.default_group'),
    OptionParser('DEBUG', 'global.debug', bool_setting),

    ]
