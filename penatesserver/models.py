# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.models import AbstractBaseUser
from django.core import validators
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.db import models
import netaddr

from penatesserver.powerdns.models import Record
from penatesserver.utils import dhcp_list_to_dict, dhcp_dict_to_list, force_bytestrings, force_bytestring, ensure_list

__author__ = 'flanker'

from ldapdb.models.fields import CharField, IntegerField, ListField
import ldapdb.models


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


class DhcpRecord(BaseLdapModel):
    base_dn = 'cn=config,ou=dhcp,ou=Services,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['dhcpHost', ])
    name = CharField(db_column=force_bytestring('cn'), primary_key=True)
    hw_address = CharField(db_column=force_bytestring('dhcpHWAddress'))  # ethernet 08:00:27:9B:3A:4D
    statements = ListField(db_column=force_bytestring('dhcpStatements'), default=[])
    options = ListField(db_column=force_bytestring('dhcpOption'))
#         'host-name',  # text
#         'fixed-address'


class DhcpSubnet(BaseLdapModel):
    base_dn = 'cn=config,ou=dhcp,ou=Services,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['dhcpSubnet', 'dhcpOptions', ])
    name = CharField(db_column=force_bytestring('cn'), primary_key=True)
    net_mask = IntegerField(db_column=force_bytestring('dhcpNetMask'))
    range = CharField(db_column=force_bytestring('dhcpRange'))
    statements = ListField(db_column=force_bytestring('dhcpStatements'), default=['default-lease-time 600', 'max-lease-time 7200', ])
    options = ListField(db_column=force_bytestring('dhcpOption'))

    def set_option(self, option_name, option_value, replace=True):
        if (self.is_v4 and option_name not in self.VALID_IP4_OPTIONS) or (self.is_v6 and option_name not in self.VALID_IP6_OPTIONS):
            return
        options = dhcp_list_to_dict(self.options)
        new_value = ensure_list(option_value)
        if replace:
            options[option_name] = new_value
        else:
            current_list = ensure_list(options.get(option_name, []))
            options[option_name] = current_list + [x for x in new_value if x not in current_list]
        self.options = dhcp_dict_to_list(options)

    @cached_property
    def is_v4(self):
        start, end = self.range.split()
        return netaddr.IPAddress(start).version == 4

    @cached_property
    def is_v6(self):
        return not self.is_v4

    def set_extra_records(self, scheme, hostname, port, fqdn, srv_field):
        ip_address = Record.local_resolve(hostname)
        if scheme == 'dns' and ip_address:
            self.set_option('domain-name-servers', ip_address)
        elif scheme == 'irc' and ip_address:
            self.set_option('irc-server', ip_address)
        elif scheme == 'ntp' and ip_address:
            self.set_option('time-servers', ip_address)
            self.set_option('ntp-servers', ip_address)
        elif scheme == 'pop3' and ip_address:
            self.set_option('pop-servers', ip_address)
        elif scheme == 'sip':
            self.set_option('dhcp6.sip-servers-names', hostname)
            if ip_address:
                self.set_option('dhcp6.sip-servers-addresses', ip_address)
        elif scheme == 'smtp' and ip_address:
            self.set_option('smtp-server', ip_address)
        elif scheme == 'tftp':
            self.set_option('tftp-server-name', hostname, replace=True)

    VALID_IP4_OPTIONS = {
        'broadcast-address',  # 'ip-address'
        'dhcp-lease-time',  # uint32
        'domain-name',  # text
        'domain-name-servers',  # 'ip-address [, ip-address... ]'
        'domain-search',  # "example.com", "sales.example.com", "eng.example.com"
        'host-name',  # text
        'irc-server',  # 'ip-address [, ip-address... ]'
        'lpr-servers',  # 'ip-address [, ip-address... ]'
        'netbios-name-servers',  # 'ip-address [, ip-address...];'
        'nis-domain',  # text
        'nis-servers',  # 'ip-address [, ip-address... ]'
        'ntp-servers',  # 'ip-address [, ip-address... ]'
        'pop-servers',  # 'ip-address [, ip-address... ]'
        'routers',  # 'ip-address [, ip-address... ]'
        'smtp-server',  # 'ip-address [, ip-address... ]'
        'subnet-mask',  # 'ip-address'
        'tftp-server-name',  # text
        'time-servers',  # 'ip-address [, ip-address... ]'
    }
    VALID_IP6_OPTIONS = {
        'dhcp6.sip-servers-names',  # domain-list
        'dhcp6.sip-servers-addresses',  # ip6-address [, ip6-address ... ]
        'dhcp6.name-servers',  # ip6-address [, ip6-address ... ] ',
        'dhcp6.domain-search',  # domain-list;'
        'dhcp6.nis-domain-name',  # text
        'dhcp6.fqdn',  # string'
    }


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


class Host(models.Model):
    fqdn = models.CharField(_('Host fqdn'), db_index=True, blank=True, default=None, null=True, max_length=255)
    owner = models.CharField(_('Owner username'), db_index=True, blank=True, default=None, null=True, max_length=255)
    main_ip_address = models.GenericIPAddressField(_('Main IP address'), db_index=True, blank=True, default=None, null=True)
    main_mac_address = models.CharField(_('Main MAC address'), db_index=True, blank=True, default=None, null=True, max_length=255)
    serial = models.CharField(_('Serial number'), db_index=True, blank=True, default=None, null=True, max_length=255)
    model_name = models.CharField(_('Model name'), db_index=True, blank=True, default=None, null=True, max_length=255)
    location = models.CharField(_('Location'), db_index=True, blank=True, default=None, null=True, max_length=255)
    os_name = models.CharField(_('OS Name'), db_index=True, blank=True, default=None, null=True, max_length=255)
    proc_model = models.CharField(_('Proc model'), db_index=True, blank=True, default=None, null=True, max_length=255)
    proc_count = models.IntegerField(_('Proc count'), db_index=True, blank=True, default=None, null=True)
    core_count = models.IntegerField(_('Core count'), db_index=True, blank=True, default=None, null=True)
    memory_size = models.IntegerField(_('Memory size'), db_index=True, blank=True, default=None, null=True)
    disk_size = models.IntegerField(_('Disk size'), db_index=True, blank=True, default=None, null=True)

    def hostname(self):
        return self.fqdn.partition('.')[0]

    def bootp_filename(self):
        return self.os_name


class Netgroup(BaseLdapModel):
    base_dn = 'ou=netgroups,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['nisNetgroup', ])
    name = CharField(db_column=force_bytestring('cn'), primary_key=True)
    triple = ListField(db_column=force_bytestring('nisNetgroupTriple'))
    member = ListField(db_column=force_bytestring('memberNisNetgroup'))


class DjangoUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('username'), max_length=250, unique=True,
                                help_text=_('Required. 30 characters or fewer. Letters, digits and "/"/@/./+/-/_ only.'),
                                validators=[validators.RegexValidator(r'^[/\w.@+_\-]+$', _('Enter a valid username. '), 'invalid'), ])
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
    scheme = models.CharField(_('Scheme'), db_index=True, blank=False, default='https', max_length=40)
    hostname = models.CharField(_('Service hostname'), db_index=True, blank=False, default='localhost', max_length=255)
    port = models.IntegerField(_('Port'), db_index=True, blank=False, default=443)
    protocol = models.CharField(_('tcp, udp or socket'), db_index=True, choices=(('tcp', 'tcp'), ('udp', 'udp'), ('socket', 'socket'), ), default='tcp', max_length=10)
    use_ssl = models.BooleanField(_('use SSL?'), db_index=True, default=False, blank=True)
    kerberos_service = models.CharField(_('Kerberos service'), blank=True, null=True, default=None, max_length=40)
    description = models.TextField(_('description'), blank=True, default='')
    dns_srv = models.CharField(_('DNS SRV field'), blank=True, null=True, default=None, max_length=90)
    status = models.IntegerField(_('Status'), default=None, null=True, blank=True, db_index=True)
    status_last_update = models.DateTimeField(_('Status last update'), default=None, null=True, blank=True, db_index=True)

    def __str__(self):
        return '%s%s://%s:%s/' % (self.scheme, 's' if self.use_ssl else '', self.hostname, self.port)

    def __unicode__(self):
        return '%s%s://%s:%s/' % (self.scheme, 's' if self.use_ssl else '', self.hostname, self.port)

    def __repr__(self):
        return 'Service("%s%s://%s:%s/")' % (self.scheme, 's' if self.use_ssl else '', self.hostname, self.port)
