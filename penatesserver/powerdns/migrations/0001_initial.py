# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import time


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=10)),
                ('modified_at', models.IntegerField()),
                ('account', models.CharField(max_length=40, null=True, blank=True)),
                ('comment', models.CharField(max_length=65535)),
            ],
            options={
                'db_table': 'comments',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='CryptoKey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flags', models.IntegerField()),
                ('active', models.NullBooleanField()),
                ('content', models.TextField(null=True, blank=True)),
            ],
            options={
                'db_table': 'cryptokeys',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('master', models.CharField(default=None, max_length=128, null=True, blank=True)),
                ('last_check', models.IntegerField(default=None, null=True, blank=True)),
                ('type', models.CharField(default='NATIVE', max_length=6)),
                ('notified_serial', models.IntegerField(default=None, null=True, blank=True)),
                ('account', models.CharField(default=None, max_length=40, null=True, blank=True)),
            ],
            options={
                'db_table': 'domains',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='DomainMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(max_length=32, null=True, blank=True)),
                ('content', models.TextField(null=True, blank=True)),
                ('domain', models.ForeignKey(blank=True, to='powerdns.Domain', null=True)),
            ],
            options={
                'db_table': 'domainMetadata',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('type', models.CharField(max_length=10, null=True, blank=True)),
                ('content', models.CharField(max_length=65535, null=True, blank=True)),
                ('ttl', models.IntegerField(default=86400, null=True, blank=True)),
                ('prio', models.IntegerField(default=0, null=True, blank=True)),
                ('change_date', models.IntegerField(default=time.time, null=True, blank=True)),
                ('disabled', models.NullBooleanField(default=False)),
                ('ordername', models.CharField(max_length=255, null=True, blank=True)),
                ('auth', models.NullBooleanField(default=True)),
                ('domain', models.ForeignKey(blank=True, to='powerdns.Domain', null=True)),
            ],
            options={
                'db_table': 'records',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Supermaster',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.GenericIPAddressField()),
                ('nameserver', models.CharField(max_length=255)),
                ('account', models.CharField(max_length=40)),
            ],
            options={
                'db_table': 'supermasters',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TSIGKey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('algorithm', models.CharField(max_length=50, null=True, blank=True)),
                ('secret', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'db_table': 'tsigkeys',
                'managed': True,
            },
        ),
        migrations.AlterUniqueTogether(
            name='tsigkey',
            unique_together=set([('name', 'algorithm')]),
        ),
        migrations.AlterUniqueTogether(
            name='supermaster',
            unique_together=set([('ip', 'nameserver')]),
        ),
        migrations.AddField(
            model_name='cryptokey',
            name='domain',
            field=models.ForeignKey(blank=True, to='powerdns.Domain', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='domain',
            field=models.ForeignKey(to='powerdns.Domain'),
        ),
    ]
