# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from djangofloor.iniconf import OptionParser

__author__ = 'Matthieu Gallet'
# noinspection PyTypeChecker
INI_MAPPING = [

    OptionParser('DATABASE_ENGINE', 'database.engine'),
    OptionParser('DATABASE_NAME', 'database.name'),
    OptionParser('DATABASE_USER', 'database.user'),
    OptionParser('DATABASE_PASSWORD', 'database.password'),
    OptionParser('DATABASE_HOST', 'database.host'),
    OptionParser('DATABASE_PORT', 'database.port'),

    OptionParser('LDAP_NAME', 'ldap.name'),
    OptionParser('LDAP_USER', 'ldap.user'),
    OptionParser('LDAP_PASSWORD', 'ldap.password'),

    OptionParser('PENATES_DOMAIN', 'penates.domain'),
    OptionParser('PENATES_COUNTRY', 'penates.country'),
    OptionParser('PENATES_ORGANIZATION', 'penates.organization'),
    OptionParser('PENATES_STATE', 'penates.state'),
    OptionParser('PENATES_LOCALITY', 'penates.locality'),
    OptionParser('PENATES_EMAIL_ADDRESS', 'penates.email_address'),

    OptionParser('SERVER_NAME', 'global.server_name'),
    OptionParser('PROTOCOL', 'global.protocol'),
    OptionParser('BIND_ADDRESS', 'global.bind_address'),
    OptionParser('LOCAL_PATH', 'global.data_path'),
    OptionParser('ADMIN_EMAIL', 'global.admin_email'),
    OptionParser('TIME_ZONE', 'global.time_zone'),
    OptionParser('LANGUAGE_CODE', 'global.language_code'),
    OptionParser('FLOOR_AUTHENTICATION_HEADER', 'global.remote_user_header'),

]
