# -*- coding=utf-8 -*-


import os

from djangofloor.deb_fixes import file_replace

__author__ = 'mgallet'


# noinspection PyUnusedLocal
def remove_unicode_literals(package_name, package_version, deb_src_dir):
    if os.path.isfile('setup.py'):
        file_replace('setup.py', 'from __future__ import unicode_literals', '')


# noinspection PyUnusedLocal
def remove_ldap_dep(package_name, package_version, deb_src_dir):
    if os.path.isfile('setup.py'):
        file_replace('setup.py', 'from __future__ import unicode_literals', '')
        # file_replace('setup.py', "'pyldap>=2.4.25',", '')
    # if os.path.isfile('ldapdb/backends/ldap/base.py'):
    #     file_replace('ldapdb/backends/ldap/base.py',
    #                  "            self.connection = ldap.initialize(self.settings_dict['NAME'], bytes_mode=False)",
    #                  "            self.connection = ldap.initialize(self.settings_dict['NAME'])")
