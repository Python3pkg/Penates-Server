# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.test import TestCase

from penatesserver.models import Principal

__author__ = 'Matthieu Gallet'


# class TestModelComputer(TestCase):
#
#     def test_computer(self):
#         fqdn = 'test.%s' % settings.PENATES_DOMAIN
#         fqdn2 = 'test2.%s' % settings.PENATES_DOMAIN
#         Computer.objects.filter(name=fqdn).delete()
#         Computer.objects.filter(name=fqdn2).delete()
#         obj = Computer(name=fqdn, uid=40000)
#         obj.save()
#         obj = Computer(name=fqdn2)
#         obj.save()
#         self.assertEqual(1, Computer.objects.filter(name=fqdn).count())
#         self.assertEqual(1, Computer.objects.filter(name=fqdn2).count())
#         Computer.objects.filter(name=fqdn).delete()
#         obj = Computer.objects.get(name=fqdn2)
#         self.assertEqual(40001, obj.uid)
#         Computer.objects.filter(name=fqdn2).delete()


class TestPrincipal(TestCase):

    def test_principal(self):
        principal_name = 'host/test.%s' % settings.PENATES_DOMAIN
        Principal.objects.filter(name=principal_name).delete()
        obj = Principal(name=principal_name)
        obj.save()
        Principal.objects.filter(name=principal_name).delete()


# class Computer(BaseLdapModel):
#     base_dn = 'ou=Computers,' + settings.LDAP_BASE_DN
#     object_classes = ['posixAccount', 'device', 'krbPrincipalAux', 'krbTicketPolicyAux']
#     name = CharField(db_column='uid', primary_key=True)
#     uid = IntegerField(db_column='uidNumber', unique=True)
#     gid = IntegerField(db_column='gidNumber', unique=False, default=1000)
#     home_directory = CharField(db_column='homeDirectory', default='/dev/null')
#     login_shell = CharField(db_column='loginShell', default='/bin/false')
#     display_name = CharField(db_column='displayName', unique=True)
#     cn = CharField(db_column='cn', unique=True)
#     serial_number = CharField(db_column='serialNumber')
#     owner = CharField(db_column='owner')
#     principal = ListField(db_column='krbPrincipalName')
