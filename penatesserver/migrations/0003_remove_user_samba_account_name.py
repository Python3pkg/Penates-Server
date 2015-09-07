# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('penatesserver', '0002_auto_20150831_0939'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='samba_account_name',
        ),
    ]
