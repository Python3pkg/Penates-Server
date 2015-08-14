# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.utils.translation import ugettext as _
from django.db import models

__author__ = 'flanker'

from ldapdb.models.fields import CharField, IntegerField, ListField
import ldapdb.models


def force_bytestrings(unicode_list):
    """
     >>> force_bytestrings([u'test'])
     ['test']
    """
    return [x.encode('utf-8') for x in unicode_list]


def force_bytestring(x):
    return x.encode('utf-8')


class BaseLdapModel(ldapdb.models.Model):
    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '%s("%s")' % (self.__class__.__name__, self.name)

    class Meta(object):
        abstract = True

    def set_next_free_value(self, attr_name, default=1000):
        if getattr(self, attr_name) is not None:
            return
        values = list(self.__class__.objects.all().order_by(b'-' + attr_name.encode('utf-8'))[0:1])
        if not values:
            setattr(self, attr_name, default)
        else:
            setattr(self, attr_name, getattr(values[0], attr_name) + 1)


class Group(BaseLdapModel):
    base_dn = 'ou=Groups,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['posixGroup', 'group'])
    # posixGroup attributes
    gid = IntegerField(db_column=force_bytestring('gidNumber'), unique=True)
    name = CharField(db_column=force_bytestring('cn'), max_length=200, primary_key=True)
    members = ListField(db_column=force_bytestring('memberUid'))
    description = CharField(db_column=force_bytestring('description'), max_length=500, blank=True, default='')

    def save(self, using=None):
        self.set_next_free_value('gid')
        super(Group, self).save(using=using)


class Service(BaseLdapModel):
    base_dn = 'ou=Services,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['ipService', ])
    name = CharField(db_column=force_bytestring('cn'), primary_key=True)
    port = IntegerField(db_column=force_bytestring('ipServicePort'), default=443)
    protocol = CharField(db_column=force_bytestring('ipServiceProtocol'), default='https')


class Principal(BaseLdapModel):
    base_dn = 'cn=krbContainer,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['krbPrincipal', 'krbPrincipalAux'])
    name = CharField(db_column=force_bytestring('krbPrincipalName'), primary_key=True)
    # principal = ListField(db_column=force_bytestring('krbPrincipalName'))


class Computer(BaseLdapModel):
    base_dn = 'ou=Computers,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['posixAccount', 'device', 'krbPrincipalAux', 'krbTicketPolicyAux'])
    name = CharField(db_column=force_bytestring('uid'), primary_key=True)
    uid = IntegerField(db_column=force_bytestring('uidNumber'), unique=True)
    gid = IntegerField(db_column=force_bytestring('gidNumber'), unique=False, default=1000)
    home_directory = CharField(db_column=force_bytestring('homeDirectory'), default='/dev/null')
    login_shell = CharField(db_column=force_bytestring('loginShell'), default='/bin/false')
    # display_name = CharField(db_column=force_bytestring('displayName'), unique=True)
    cn = CharField(db_column=force_bytestring('cn'), unique=True)
    serial_number = CharField(db_column=force_bytestring('serialNumber'))
    owner = CharField(db_column=force_bytestring('owner'))
    # principal = ListField(db_column=force_bytestring('krbPrincipalName'))

    def save(self, using=None):
        # self.display_name = self.name.upper()
        self.cn = self.name.upper()
        self.set_next_free_value('uid')
        super(Computer, self).save(using=using)


class Netgroup(BaseLdapModel):
    base_dn = 'ou=netgroups,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['nisNetgroup', ])
    name = CharField(db_column=force_bytestring('cn'), primary_key=True)
    triple = ListField(db_column=force_bytestring('nisNetgroupTriple'))
    member = ListField(db_column=force_bytestring('memberNisNetgroup'))

