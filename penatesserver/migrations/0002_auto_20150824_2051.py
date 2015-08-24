# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ldapdb.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('penatesserver', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'uid')),
                ('display_name', ldapdb.models.fields.CharField(max_length=200, db_column=b'displayName')),
                ('uid_number', ldapdb.models.fields.IntegerField(default=None, db_column=b'uidNumber')),
                ('gid_number', ldapdb.models.fields.IntegerField(default=None, db_column=b'gidNumber')),
                ('login_shell', ldapdb.models.fields.CharField(default='/bin/bash', max_length=200, db_column=b'loginShell')),
                ('description', ldapdb.models.fields.CharField(default='Description', max_length=200, db_column=b'description')),
                ('jpeg_photo', ldapdb.models.fields.ImageField(db_column=b'jpegPhoto')),
                ('phone', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'telephoneNumber')),
                ('samba_acct_flags', ldapdb.models.fields.CharField(default='[UX         ]', max_length=200, db_column=b'sambaAcctFlags')),
                ('samba_sid', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'sambaSID')),
                ('user_smime_certificate', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'userSMIMECertificate')),
                ('user_certificate', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'userCertificate')),
                ('home_directory', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'homeDirectory')),
                ('mail', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'mail')),
                ('samba_domain_name', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'sambaDomainName')),
                ('gecos', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'gecos')),
                ('cn', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'cn')),
                ('user_password', ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'userPassword')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='Computer',
        ),
        migrations.DeleteModel(
            name='DhcpRecord',
        ),
        migrations.DeleteModel(
            name='DhcpSubnet',
        ),
    ]
