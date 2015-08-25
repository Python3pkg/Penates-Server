# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import ldapdb.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('penatesserver', '0002_auto_20150824_2051'),
    ]

    operations = [
        migrations.CreateModel(
            name='SambaDomain',
            fields=[
                ('dn', models.CharField(max_length=200)),
                ('rid_base', ldapdb.models.fields.IntegerField(default=1000, db_column=b'sambaAlgorithmicRidBase')),
                ('sid', ldapdb.models.fields.CharField(max_length=200, db_column=b'sambaSID')),
                ('name', ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'sambaDomainName')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='group',
            name='group_type',
            field=ldapdb.models.fields.IntegerField(default=2, db_column=b'sambaGroupType'),
        ),
        migrations.AddField(
            model_name='group',
            name='samba_sid',
            field=ldapdb.models.fields.CharField(default='', unique=True, max_length=200, db_column=b'sambaSID'),
        ),
        migrations.AddField(
            model_name='principal',
            name='flags',
            field=ldapdb.models.fields.IntegerField(default=128, db_column=b'krbTicketFlags'),
        ),
        migrations.AddField(
            model_name='user',
            name='primary_group_samba_sid',
            field=ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'sambaPrimaryGroupSID'),
        ),
        migrations.AddField(
            model_name='user',
            name='sn',
            field=ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'sn', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')]),
        ),
        migrations.AlterField(
            model_name='group',
            name='name',
            field=ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'cn', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='cn',
            field=ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'cn', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=ldapdb.models.fields.CharField(max_length=200, serialize=False, primary_key=True, db_column=b'uid', validators=[django.core.validators.RegexValidator('^[a-zA-Z][\\w_]{0,199}$')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='uid_number',
            field=ldapdb.models.fields.IntegerField(default=None, unique=True, db_column=b'uidNumber'),
        ),
    ]
