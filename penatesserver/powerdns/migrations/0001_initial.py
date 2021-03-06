# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-05 08:45


from django.db import migrations, models
import time


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=10)),
                ('modified_at', models.IntegerField()),
                ('account', models.CharField(blank=True, max_length=40, null=True)),
                ('comment', models.CharField(max_length=65535)),
            ],
            options={
                'db_table': 'comments',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CryptoKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flags', models.IntegerField()),
                ('active', models.NullBooleanField()),
                ('content', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cryptokeys',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('master', models.CharField(blank=True, default=None, max_length=128, null=True)),
                ('last_check', models.IntegerField(blank=True, default=None, null=True)),
                ('type', models.CharField(default='NATIVE', max_length=6)),
                ('notified_serial', models.IntegerField(blank=True, default=None, null=True)),
                ('account', models.CharField(blank=True, default=None, max_length=40, null=True)),
            ],
            options={
                'db_table': 'domains',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DomainMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(blank=True, max_length=32, null=True)),
                ('content', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'domainMetadata',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('type', models.CharField(blank=True, max_length=10, null=True)),
                ('content', models.CharField(blank=True, max_length=65535, null=True)),
                ('ttl', models.IntegerField(blank=True, default=86400, null=True)),
                ('prio', models.IntegerField(blank=True, default=0, null=True)),
                ('change_date', models.IntegerField(blank=True, default=time.time, null=True)),
                ('disabled', models.NullBooleanField(default=False)),
                ('ordername', models.CharField(blank=True, max_length=255, null=True)),
                ('auth', models.NullBooleanField(default=True)),
            ],
            options={
                'db_table': 'records',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Supermaster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField()),
                ('nameserver', models.CharField(max_length=255)),
                ('account', models.CharField(max_length=40)),
            ],
            options={
                'db_table': 'supermasters',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TSIGKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('algorithm', models.CharField(blank=True, max_length=50, null=True)),
                ('secret', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'tsigkeys',
                'managed': False,
            },
        ),
    ]
