# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import ldapdb.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('penatesserver', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('username', models.CharField(unique=True, max_length=250, verbose_name="nom d'utilisateur", validators=[django.core.validators.RegexValidator('^[/\\w.@+_\\-]+$', 'Enter a valid username. ', 'invalid')])),
                ('user_permissions', models.ManyToManyField(related_query_name='admin_user', related_name='admin_user_set', to='auth.Permission')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
