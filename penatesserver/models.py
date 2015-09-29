# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import os

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.models import AbstractBaseUser
from django.core import validators
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.lru_cache import lru_cache
from django.utils.translation import ugettext as _
from django.db import models

from penatesserver.kerb import change_password, delete_principal, add_principal
from penatesserver.pki.constants import USER, EMAIL, SIGNATURE, ENCIPHERMENT
from penatesserver.pki.service import CertificateEntry
from penatesserver.powerdns.models import Record
from penatesserver.utils import force_bytestrings, force_bytestring, password_hash, ensure_location

__author__ = 'flanker'

from ldapdb.models.fields import CharField, IntegerField, ListField, ImageField as ImageField_
import ldapdb.models

name_pattern = r'[a-zA-Z][\w_]{0,199}'
name_validators = [RegexValidator('^%s$' % name_pattern)]


class ImageField(ImageField_):
    def get_internal_type(self):
        return 'CharField'


class BaseLdapModel(ldapdb.models.Model):
    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '%s("%s")' % (self.__class__.__name__, self.name)

    class Meta(object):
        abstract = True

    def set_next_free_value(self, attr_name, default=2000):
        if getattr(self, attr_name) is not None:
            return
        values = list(self.__class__.objects.all().order_by(b'-' + attr_name.encode('utf-8'))[0:1])
        if not values:
            setattr(self, attr_name, default)
        else:
            setattr(self, attr_name, getattr(values[0], attr_name) + 1)


class SambaDomain(BaseLdapModel):
    base_dn = settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['sambaDomain'])
    rid_base = IntegerField(db_column=force_bytestring('sambaAlgorithmicRidBase'), default=2000)
    sid = CharField(db_column=force_bytestring('sambaSID'))
    name = CharField(db_column=force_bytestring('sambaDomainName'), primary_key=True)


# noinspection PyCallingNonCallable
@lru_cache()
def get_samba_sid():
    return SambaDomain.objects.all()[0].sid


class Group(BaseLdapModel):
    base_dn = 'ou=Groups,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['posixGroup', 'sambaGroupMapping'])
    # posixGroup attributes
    name = CharField(db_column=force_bytestring('cn'), max_length=200, primary_key=True, validators=list(name_validators))
    gid = IntegerField(db_column=force_bytestring('gidNumber'), unique=True)
    members = ListField(db_column=force_bytestring('memberUid'))
    description = CharField(db_column=force_bytestring('description'), max_length=500, blank=True, default='')
    group_type = IntegerField(db_column=force_bytestring('sambaGroupType'), default=None)
    samba_sid = CharField(db_column=force_bytestring('sambaSID'), unique=True, default='')

    def save(self, using=None):
        self.group_type = 2
        self.set_next_free_value('gid', default=10000)
        self.samba_sid = '%s-%d' % (get_samba_sid(), self.gid)
        super(Group, self).save(using=using)
        group_of_names = list(GroupOfNames.objects.filter(name=self.name)[0:1])
        if not group_of_names:
            group = GroupOfNames(name=self.name, members=['cn=admin,' + settings.LDAP_BASE_DN])
            group.save()
        else:
            group = group_of_names[0]
        new_members = ['cn=admin,' + settings.LDAP_BASE_DN] + ['uid=%s,%s' % (x, User.base_dn) for x in self.members]
        if new_members != group.members:
            group.members = new_members
            group.save()


class GroupOfNames(BaseLdapModel):
    base_dn = 'ou=CoreGroups,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['groupOfNames'])
    name = CharField(db_column=force_bytestring('cn'), max_length=200, primary_key=True, validators=list(name_validators))
    members = ListField(db_column=force_bytestring('member'))


class User(BaseLdapModel):
    base_dn = 'ou=Users,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['posixAccount', 'shadowAccount', 'inetOrgPerson', 'sambaSamAccount', 'person', 'AsteriskSIPUser'])
    name = CharField(db_column=force_bytestring('uid'), max_length=200, primary_key=True, validators=list(name_validators))
    display_name = CharField(db_column=force_bytestring('displayName'), max_length=200)
    uid_number = IntegerField(db_column=force_bytestring('uidNumber'), default=None, unique=True)
    gid_number = IntegerField(db_column=force_bytestring('gidNumber'), default=None)
    login_shell = CharField(db_column=force_bytestring('loginShell'), default='/bin/bash')
    description = CharField(db_column=force_bytestring('description'), default='Description')
    jpeg_photo = ImageField(db_column=force_bytestring('jpegPhoto'), max_length=10000000)
    phone = CharField(db_column=force_bytestring('telephoneNumber'), default=None)
    samba_acct_flags = CharField(db_column=force_bytestring('sambaAcctFlags'), default='[UX         ]')
    user_smime_certificate = CharField(db_column=force_bytestring('userSMIMECertificate'), default=None)
    user_certificate = CharField(db_column=force_bytestring('userCertificate'), default=None)
    # forced values
    samba_sid = CharField(db_column=force_bytestring('sambaSID'), default=None)
    primary_group_samba_sid = CharField(db_column=force_bytestring('sambaPrimaryGroupSID'), default=None)
    home_directory = CharField(db_column=force_bytestring('homeDirectory'), default=None)
    mail = CharField(db_column=force_bytestring('mail'), default=None)
    samba_domain_name = CharField(db_column=force_bytestring('sambaDomainName'), default=None)
    gecos = CharField(db_column=force_bytestring('gecos'), max_length=200, default=None)
    cn = CharField(db_column=force_bytestring('cn'), max_length=200, default=None, validators=list(name_validators))
    sn = CharField(db_column=force_bytestring('sn'), max_length=200, default=None, validators=list(name_validators))
    # password values
    user_password = CharField(db_column=force_bytestring('userPassword'), default=None)
    # samba_nt_password = CharField(db_column=force_bytestring('sambaNTPassword'), default=None)
    ast_account_caller_id = CharField(db_column=force_bytestring('AstAccountCallerID'), default=None)
    ast_account_context = CharField(db_column=force_bytestring('AstAccountContext'), default='LocalSets')
    ast_account_DTMF_mode = CharField(db_column=force_bytestring('AstAccountDTMFMode'), default='rfc2833')
    ast_account_mailbox = CharField(db_column=force_bytestring('AstAccountMailbox'), default=None)
    ast_account_NAT = CharField(db_column=force_bytestring('AstAccountNAT'), default='yes')
    ast_account_qualify = CharField(db_column=force_bytestring('AstAccountQualify'), default='yes')
    ast_account_type = CharField(db_column=force_bytestring('AstAccountType'), default='friend')
    ast_account_disallowed_codec = CharField(db_column=force_bytestring('AstAccountDisallowedCodec'), default='all')
    ast_account_allowed_codec = CharField(db_column=force_bytestring('AstAccountAllowedCodec'), default='ulaw')
    ast_account_music_on_hold = CharField(db_column=force_bytestring('AstAccountMusicOnHold'), default='default')

    def save(self, using=None):
        group = self.set_gid_number()
        self.cn = self.name
        self.sn = self.name
        self.gecos = self.display_name
        self.ast_account_caller_id = self.display_name
        self.samba_domain_name = settings.PENATES_REALM
        self.mail = '%s@%s' % (self.name, settings.PENATES_DOMAIN)
        self.ast_account_mailbox = self.mail
        self.home_directory = '/home/%s' % self.name
        self.set_next_free_value('uid_number')
        self.samba_sid = '%s-%d' % (get_samba_sid(), self.uid_number)
        self.primary_group_samba_sid = '%s-%d' % (get_samba_sid(), self.gid_number)
        super(User, self).save(using=using)
        if group and self.name not in group.members:
            group.members.append(self.name)
            group.save()
        add_principal(self.principal_name)

    @property
    def principal_name(self):
        return '%s@%s' % (self.name, settings.PENATES_REALM)

    def set_gid_number(self):
        if self.gid_number is not None:
            groups = list(Group.objects.filter(gid=self.gid_number)[0:1])
        else:
            groups = list(Group.objects.filter(name=self.name)[0:1])
        if not groups:
            group = Group(name=self.name, gid=self.gid_number)
            group.save()
        else:
            group = groups[0]
        self.gid_number = group.gid
        return group

    def set_password(self, password):
        self.user_password = password_hash(password)
        self.save()
        change_password(self.principal_name, password)
        if settings.STORE_CLEARTEXT_PASSWORDS:
            ensure_location(self.password_filename)
            with codecs.open(self.password_filename, 'w', encoding='utf-8') as fd:
                fd.write(password)
            os.chmod(self.password_filename, 0o400)

    @property
    def password_filename(self):
        return os.path.join(settings.PKI_PATH, 'private', 'passwords', self.name + '.txt')

    def read_password(self):
        if settings.STORE_CLEARTEXT_PASSWORDS:
            with codecs.open(self.password_filename, 'r', encoding='utf-8') as fd:
                return fd.read()
        return ''

    def delete(self, using=None):
        super(User, self).delete(using=using)
        delete_principal(self.principal_name)

    @property
    def user_certificate_entry(self):
        return CertificateEntry(self.name, organizationName=settings.PENATES_ORGANIZATION, organizationalUnitName=_('Users'),
                                emailAddress=self.mail, localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                                stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=USER)

    @property
    def email_certificate_entry(self):
        return CertificateEntry(self.name, organizationName=settings.PENATES_ORGANIZATION, organizationalUnitName=_('Users'),
                                emailAddress=self.mail, localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                                stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=EMAIL)

    @property
    def signature_certificate_entry(self):
        return CertificateEntry(self.name, organizationName=settings.PENATES_ORGANIZATION, organizationalUnitName=_('Users'),
                                emailAddress=self.mail, localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                                stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=SIGNATURE)

    @property
    def encipherment_certificate_entry(self):
        return CertificateEntry(self.name, organizationName=settings.PENATES_ORGANIZATION, organizationalUnitName=_('Users'),
                                emailAddress=self.mail, localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                                stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=ENCIPHERMENT)


class Principal(BaseLdapModel):
    base_dn = 'cn=krbContainer,' + settings.LDAP_BASE_DN
    object_classes = force_bytestrings(['krbPrincipal', 'krbPrincipalAux', 'krbTicketPolicyAux'])
    name = CharField(db_column=force_bytestring('krbPrincipalName'), primary_key=True)
    flags = IntegerField(db_column=force_bytestring('krbTicketFlags'), default=None)

    def save(self, using=None):
        self.flags = 128
        super(Principal, self).save(using=using)


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


class Partition(models.Model):
    host = models.ForeignKey(Host, db_index=True)
    mount_point = models.CharField(_('mount point'), max_length=255, default='/')
    device = models.CharField(_('device'), max_length=255, default='/dev')
    fs_type = models.CharField(_('fs type'), max_length=100, default='ext2')
    options = models.CharField(_('options'), max_length=100, blank=True, default='')


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
    protocol = models.CharField(_('tcp, udp or socket'), db_index=True, choices=(('tcp', 'tcp'), ('udp', 'udp'), ('socket', 'socket'),), default='tcp', max_length=10)
    encryption = models.CharField(_('encryption'), db_index=True,
                                  choices=(('none', _('No encryption')), ('tls', _('SSL/TLS')),
                                           ('starttls', _('START TLS')), ), max_length=10, default='none')
    kerberos_service = models.CharField(_('Kerberos service'), blank=True, null=True, default=None, max_length=40)
    description = models.TextField(_('description'), blank=True, default=_('Service'))
    dns_srv = models.CharField(_('DNS SRV field'), blank=True, null=True, default=None, max_length=90)
    status = models.IntegerField(_('Status'), default=None, null=True, blank=True, db_index=True)
    status_last_update = models.DateTimeField(_('Status last update'), default=None, null=True, blank=True, db_index=True)

    def __str__(self):
        return '%s://%s:%s/' % (self.scheme, self.hostname, self.port)

    def __unicode__(self):
        return '%s://%s:%s/' % (self.scheme, self.hostname, self.port)

    def __repr__(self):
        return 'Service("%s://%s:%s/")' % (self.scheme, self.hostname, self.port)
