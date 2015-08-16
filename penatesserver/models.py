# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.models import AbstractBaseUser
from django.core import validators
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.db import models

__author__ = 'flanker'

from ldapdb.models.fields import CharField, IntegerField, ListField
import ldapdb.models


def force_bytestrings(unicode_list):
    """
     >>> force_bytestrings(['test'])
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


class Principal(BaseLdapModel):
    base_dn = 'cn=krbContainer,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['krbPrincipal', 'krbPrincipalAux', 'krbTicketPolicyAux'])
    name = CharField(db_column=force_bytestring('krbPrincipalName'), primary_key=True)
    # principal = ListField(db_column=force_bytestring('krbPrincipalName'))


class Computer(BaseLdapModel):
    base_dn = 'ou=Computers,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['posixAccount', 'device'])
    name = CharField(db_column=force_bytestring('uid'), primary_key=True)
    uid = IntegerField(db_column=force_bytestring('uidNumber'), unique=True)
    gid = IntegerField(db_column=force_bytestring('gidNumber'), unique=False, default=1000)
    home_directory = CharField(db_column=force_bytestring('homeDirectory'), default='/dev/null')
    login_shell = CharField(db_column=force_bytestring('loginShell'), default='/bin/false')
    cn = CharField(db_column=force_bytestring('cn'), unique=True)
    serial_number = CharField(db_column=force_bytestring('serialNumber'))
    owner = CharField(db_column=force_bytestring('owner'))

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


class DjangoUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('username'), max_length=250, unique=True,
                                help_text=_('Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                                validators=[validators.RegexValidator(r'^[\w.@+-]+$',
                                                                      _('Enter a valid username. '
                                                                        'This value may contain only letters, numbers '
                                                                        'and @/./+/-/_ characters.'), 'invalid'), ])
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta(object):
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)


class Service(models.Model):
    fqdn = models.CharField(_('Host fqdn'), db_index=True, blank=True, default=None, null=True, max_length=255)
    protocol = models.CharField(_('Protocol'), db_index=True, blank=False, default='https', max_length=40)
    hostname = models.CharField(_('Hostname'), db_index=True, blank=False, default=settings.SERVER_NAME, max_length=255)
    port = models.IntegerField(_('Port'), db_index=True, blank=False, default=443)
    kerberos_service = models.CharField(_('Kerberos service'), blank=True, null=True, default=None, max_length=40)
    description = models.TextField(_('description'), blank=True, default='')
