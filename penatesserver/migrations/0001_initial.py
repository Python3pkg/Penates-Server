# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
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
            name='Computer',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'uid')),
                ('uid', ldapdb.models.fields.IntegerField(unique=True, db_column=b'uidNumber')),
                ('gid', ldapdb.models.fields.IntegerField(default=1000, db_column=b'gidNumber')),
                ('home_directory', ldapdb.models.fields.CharField(default='/dev/null', max_length=200, db_column=b'homeDirectory')),
                ('login_shell', ldapdb.models.fields.CharField(default='/bin/false', max_length=200, db_column=b'loginShell')),
                ('cn', ldapdb.models.fields.CharField(unique=True, max_length=200, db_column=b'cn')),
                ('serial_number', ldapdb.models.fields.CharField(max_length=200, db_column=b'serialNumber')),
                ('owner', ldapdb.models.fields.CharField(max_length=200, db_column=b'owner')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DhcpRecord',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'cn')),
                ('hw_address', ldapdb.models.fields.CharField(max_length=200, db_column=b'dhcpHWAddress')),
                ('statements', ldapdb.models.fields.ListField(default=[], db_column=b'dhcpStatements')),
                ('options', ldapdb.models.fields.ListField(db_column=b'dhcpOption')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DhcpSubnet',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'cn')),
                ('net_mask', ldapdb.models.fields.IntegerField(db_column=b'dhcpNetMask')),
                ('range', ldapdb.models.fields.CharField(max_length=200, db_column=b'dhcpRange')),
                ('statements', ldapdb.models.fields.ListField(default=['default-lease-time 600', 'max-lease-time 7200'], db_column=b'dhcpStatements')),
                ('options', ldapdb.models.fields.ListField(db_column=b'dhcpOption')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('gid', ldapdb.models.fields.IntegerField(unique=True, db_column=b'gidNumber')),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'cn')),
                ('members', ldapdb.models.fields.ListField(db_column=b'memberUid')),
                ('description', ldapdb.models.fields.CharField(default='', max_length=500, db_column=b'description', blank=True)),
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
                ('serial', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Serial number', db_index=True)),
                ('model_name', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Model name', db_index=True)),
                ('location', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Emplacement', db_index=True)),
                ('os_name', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='OS Name', db_index=True)),
                ('proc_model', models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Proc model', db_index=True)),
                ('proc_count', models.IntegerField(default=None, null=True, verbose_name='Proc count', db_index=True, blank=True)),
                ('core_count', models.IntegerField(default=None, null=True, verbose_name='Core count', db_index=True, blank=True)),
                ('memory_size', models.IntegerField(default=None, null=True, verbose_name='Memory size', db_index=True, blank=True)),
                ('disk_size', models.IntegerField(default=None, null=True, verbose_name='Disk size', db_index=True, blank=True)),
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
                ('use_ssl', models.BooleanField(default=False, db_index=True, verbose_name='use SSL?')),
                ('kerberos_service', models.CharField(default=None, max_length=40, null=True, verbose_name='Kerberos service', blank=True)),
                ('description', models.TextField(default='', verbose_name='description', blank=True)),
                ('dns_srv', models.CharField(default=None, max_length=90, null=True, verbose_name='DNS SRV field', blank=True)),
                ('status', models.IntegerField(default=None, null=True, verbose_name='Status', db_index=True, blank=True)),
                ('status_last_update', models.DateTimeField(default=None, null=True, verbose_name='Status last update', db_index=True, blank=True)),
            ],
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
