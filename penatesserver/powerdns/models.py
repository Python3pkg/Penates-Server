# -*- coding: utf-8 -*-
from __future__ import unicode_literals
__author__ = 'Matthieu Gallet'


from django.db import models


class Comment(models.Model):
    domain = models.ForeignKey('Domain')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10)
    modified_at = models.IntegerField()
    account = models.CharField(max_length=40, blank=True, null=True)
    comment = models.CharField(max_length=65535)

    class Meta(object):
        managed = False
        db_table = 'comments'


class CryptoKey(models.Model):
    domain = models.ForeignKey('Domain', blank=True, null=True)
    flags = models.IntegerField()
    active = models.NullBooleanField()
    content = models.TextField(blank=True, null=True)

    class Meta(object):
        managed = False
        db_table = 'cryptokeys'


class DomainMetadata(models.Model):
    domain = models.ForeignKey('Domain', blank=True, null=True)
    kind = models.CharField(max_length=32, blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    class Meta(object):
        managed = False
        db_table = 'domainMetadata'


class Domain(models.Model):
    name = models.CharField(unique=True, max_length=255)
    master = models.CharField(max_length=128, blank=True, null=True, default=None)
    last_check = models.IntegerField(blank=True, null=True, default=None)
    type = models.CharField(max_length=6, default='NATIVE')
    notified_serial = models.IntegerField(blank=True, null=True, default=None)
    account = models.CharField(max_length=40, blank=True, null=True, default=None)

    class Meta(object):
        managed = False
        db_table = 'domains'


class Record(models.Model):
    domain = models.ForeignKey(Domain, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=10, blank=True, null=True)
    content = models.CharField(max_length=65535, blank=True, null=True)
    ttl = models.IntegerField(blank=True, null=True)
    prio = models.IntegerField(blank=True, null=True)
    change_date = models.IntegerField(blank=True, null=True)
    disabled = models.NullBooleanField()
    ordername = models.CharField(max_length=255, blank=True, null=True)
    auth = models.NullBooleanField()

    class Meta(object):
        managed = False
        db_table = 'records'


class Supermaster(models.Model):
    ip = models.GenericIPAddressField()
    nameserver = models.CharField(max_length=255)
    account = models.CharField(max_length=40)

    class Meta(object):
        managed = False
        db_table = 'supermasters'
        unique_together = (('ip', 'nameserver'), )


class TSIGKey(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    algorithm = models.CharField(max_length=50, blank=True, null=True)
    secret = models.CharField(max_length=255, blank=True, null=True)

    class Meta(object):
        managed = False
        db_table = 'tsigkeys'
        unique_together = (('name', 'algorithm'), )
