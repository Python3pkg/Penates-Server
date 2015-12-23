# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import penatesserver.models
import django.contrib.auth.models
import django.utils.timezone
import django.core.validators
import ldapdb.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='DjangoUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(help_text='Required. 30 characters or fewer. Letters, digits and "/"/@/./+/-/_ only.', unique=True, max_length=250, verbose_name="nom d'utilisateur", validators=[django.core.validators.RegexValidator('^[/\\w.@+_\\-]+$', 'Enter a valid username. ', 'invalid')])),
                ('first_name', models.CharField(max_length=30, verbose_name='pr\xe9nom', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='nom', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='adresse \xe9lectronique', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text="Pr\xe9cise si l'utilisateur peut se connecter \xe0 ce site d'administration.", verbose_name='statut \xe9quipe')),
                ('is_active', models.BooleanField(default=True, help_text="Pr\xe9cise si l'utilisateur doit \xeatre consid\xe9r\xe9 comme actif. D\xe9cochez ceci plut\xf4t que de supprimer le compte.", verbose_name='actif')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name="date d'inscription")),
            ],
            options={
                'verbose_name': 'utilisateur',
                'verbose_name_plural': 'utilisateurs',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'cn', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')])),
                ('gid', ldapdb.models.fields.IntegerField(unique=True, db_column=b'gidNumber')),
                ('members', ldapdb.models.fields.ListField(db_column=b'memberUid')),
                ('description', ldapdb.models.fields.CharField(default='', max_length=500, db_column=b'description', blank=True)),
                ('group_type', ldapdb.models.fields.IntegerField(default=None, db_column=b'sambaGroupType')),
                ('samba_sid', ldapdb.models.fields.CharField(default='', unique=True, max_length=200, db_column=b'sambaSID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GroupOfNames',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'cn', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')])),
                ('members', ldapdb.models.fields.ListField(db_column=b'member')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fqdn', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Host fqdn', db_index=True)),
                ('owner', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Owner username', db_index=True)),
                ('main_ip_address', models.GenericIPAddressField(default=None, blank=True, null=True, verbose_name='Main IP address', db_index=True)),
                ('main_mac_address', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Main MAC address', db_index=True)),
                ('admin_ip_address', models.GenericIPAddressField(default=None, blank=True, null=True, verbose_name='Admin IP address', db_index=True)),
                ('admin_mac_address', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Admin MAC address', db_index=True)),
                ('serial', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Serial number', db_index=True)),
                ('model_name', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Model name', db_index=True)),
                ('location', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Emplacement', db_index=True)),
                ('os_name', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='OS Name', db_index=True)),
                ('bootp_filename', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='BootP filename')),
                ('proc_model', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Proc model', db_index=True)),
                ('proc_count', models.IntegerField(default=None, null=True, verbose_name='Proc count', db_index=True, blank=True)),
                ('core_count', models.IntegerField(default=None, null=True, verbose_name='Core count', db_index=True, blank=True)),
                ('memory_size', models.IntegerField(default=None, null=True, verbose_name='Memory size', db_index=True, blank=True)),
                ('disk_size', models.IntegerField(default=None, null=True, verbose_name='Disk size', db_index=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='MountPoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mount_point', models.CharField(default='/', max_length=255, verbose_name='mount point')),
                ('device', models.CharField(default='/dev', max_length=255, verbose_name='device')),
                ('fs_type', models.CharField(default='ext2', max_length=100, verbose_name='fs type')),
                ('options', models.CharField(default='', max_length=100, verbose_name='options', blank=True)),
                ('host', models.ForeignKey(to='penatesserver.Host')),
            ],
        ),
        migrations.CreateModel(
            name='Netgroup',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'cn')),
                ('triple', ldapdb.models.fields.ListField(db_column=b'nisNetgroupTriple')),
                ('member', ldapdb.models.fields.ListField(db_column=b'memberNisNetgroup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Principal',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'krbPrincipalName')),
                ('flags', ldapdb.models.fields.IntegerField(default=None, db_column=b'krbTicketFlags')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PrincipalTest',
            fields=[
                ('name', models.CharField(max_length=255, serialize=False, primary_key=True, db_index=True)),
                ('flags', models.IntegerField(default=None, null=True, db_index=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SambaDomain',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('rid_base', ldapdb.models.fields.IntegerField(default=2000, db_column=b'sambaAlgorithmicRidBase')),
                ('sid', ldapdb.models.fields.CharField(max_length=200, db_column=b'sambaSID')),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'sambaDomainName')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fqdn', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Host fqdn', db_index=True)),
                ('scheme', models.CharField(default='https', max_length=40, verbose_name='Scheme', db_index=True)),
                ('hostname', models.CharField(default='localhost', max_length=255, verbose_name='Service hostname', db_index=True)),
                ('port', models.IntegerField(default=443, verbose_name='Port', db_index=True)),
                ('protocol', models.CharField(default='tcp', max_length=10, verbose_name='tcp, udp or socket', db_index=True, choices=[('tcp', 'tcp'), ('udp', 'udp'), ('socket', 'socket')])),
                ('encryption', models.CharField(default='none', max_length=10, verbose_name='encryption', db_index=True, choices=[('none', 'No encryption'), ('tls', 'SSL/TLS'), ('starttls', 'START TLS')])),
                ('kerberos_service', models.CharField(default=None, max_length=40, null=True, verbose_name='Kerberos service', blank=True)),
                ('description', models.TextField(default='Service', verbose_name='description', blank=True)),
                ('dns_srv', models.CharField(default=None, max_length=90, null=True, verbose_name='DNS SRV field', blank=True)),
                ('status', models.IntegerField(default=None, null=True, verbose_name='Status', db_index=True, blank=True)),
                ('status_last_update', models.DateTimeField(default=None, null=True, verbose_name='Status last update', db_index=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'uid', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')])),
                ('display_name', ldapdb.models.fields.CharField(max_length=200, db_column=b'displayName')),
                ('uid_number', ldapdb.models.fields.IntegerField(default=None, unique=True, db_column=b'uidNumber')),
                ('gid_number', ldapdb.models.fields.IntegerField(default=None, db_column=b'gidNumber')),
                ('login_shell', ldapdb.models.fields.CharField(default='/bin/bash', max_length=200, db_column=b'loginShell')),
                ('description', ldapdb.models.fields.CharField(default='Description', max_length=200, db_column=b'description')),
                ('jpeg_photo', penatesserver.models.ImageField(max_length=10000000, db_column=b'jpegPhoto')),
                ('phone', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'telephoneNumber')),
                ('samba_acct_flags', ldapdb.models.fields.CharField(default='[UX         ]', max_length=200, db_column=b'sambaAcctFlags')),
                ('user_smime_certificate', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'userSMIMECertificate')),
                ('user_certificate', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'userCertificate')),
                ('samba_sid', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'sambaSID')),
                ('primary_group_samba_sid', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'sambaPrimaryGroupSID')),
                ('home_directory', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'homeDirectory')),
                ('mail', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'mail')),
                ('samba_domain_name', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'sambaDomainName')),
                ('gecos', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'gecos')),
                ('cn', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'cn', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')])),
                ('sn', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'sn', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')])),
                ('user_password', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'userPassword')),
                ('ast_account_caller_id', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'AstAccountCallerID')),
                ('ast_account_context', ldapdb.models.fields.CharField(default='LocalSets', max_length=200, db_column=b'AstAccountContext')),
                ('ast_account_DTMF_mode', ldapdb.models.fields.CharField(default='rfc2833', max_length=200, db_column=b'AstAccountDTMFMode')),
                ('ast_account_mailbox', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'AstAccountMailbox')),
                ('ast_account_NAT', ldapdb.models.fields.CharField(default='yes', max_length=200, db_column=b'AstAccountNAT')),
                ('ast_account_qualify', ldapdb.models.fields.CharField(default='yes', max_length=200, db_column=b'AstAccountQualify')),
                ('ast_account_type', ldapdb.models.fields.CharField(default='friend', max_length=200, db_column=b'AstAccountType')),
                ('ast_account_disallowed_codec', ldapdb.models.fields.CharField(default='all', max_length=200, db_column=b'AstAccountDisallowedCodec')),
                ('ast_account_allowed_codec', ldapdb.models.fields.CharField(default='ulaw', max_length=200, db_column=b'AstAccountAllowedCodec')),
                ('ast_account_music_on_hold', ldapdb.models.fields.CharField(default='default', max_length=200, db_column=b'AstAccountMusicOnHold')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='djangouser',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='djangouser',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
    ]
