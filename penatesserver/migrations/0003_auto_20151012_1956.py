# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import ldapdb.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('penatesserver', '0002_auto_20151012_0753'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adminuser',
            options={'permissions': (('administration', 'can administrate services'), ('supervision', 'can get supervision configuration'), ('dhcp', 'can get DHCP configuration'))},
        ),
    ]
