# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import ldapdb.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('penatesserver', '0001_initial'),
    ]

    operations = [
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
        migrations.AddField(
            model_name='user',
            name='samba_account_name',
            field=ldapdb.models.fields.CharField(default=None, max_length=200, db_column=b'samAccountName'),
        ),
    ]
