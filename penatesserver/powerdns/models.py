# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import re
import time
from django.conf import settings
import netaddr

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

    @staticmethod
    def default_record_values(ttl=86400, prio=0, disabled=False, auth=True, change_date=None):
        return {'ttl': ttl, 'prio': prio, 'disabled': disabled, 'auth': auth, 'change_date': change_date or time.time()}

    def set_extra_records(self, protocol, hostname, port, fqdn, srv_field):
        if protocol == 'dns':
            Record.objects.get_or_create(defaults=self.default_record_values(), domain=self, type='NS', name=self.name, content=hostname)
            if Record.objects.filter(domain=self, type='SOA').count() == 0:
                content = '%s %s %s 10800 3600 604800 3600' % (hostname, settings.PENATES_EMAIL_ADDRESS, self.get_soa_serial())
                Record.objects.get_or_create(defaults=self.default_record_values(), domain=self, type='SOA', name=self.name, content=content)
        elif protocol == 'smtp':
            content = '10 %s' % hostname
            Record.objects.get_or_create(defaults=self.default_record_values(), domain=self, type='MX', name=self.name, content=content)
        if srv_field:
            matcher_full = re.match(r'^(\w+)/(\w+):(\d+):(\d+)$', srv_field)
            matcher_protocol = re.match(r'^(\w+)/(\w+)$', srv_field)
            matcher_service = re.match(r'^(\w+)$', srv_field)
            if matcher_full:
                self.ensure_srv_record(matcher_full.group(1), matcher_full.group(2), port, int(matcher_full.group(3)), int(matcher_full.group(4)), fqdn)
            elif matcher_protocol:
                self.ensure_srv_record(matcher_protocol.group(1), matcher_protocol.group(2), port, 0, 100, fqdn)
            elif matcher_service:
                self.ensure_srv_record('tcp', matcher_service.group(2), port, 0, 100, fqdn)

    @staticmethod
    def get_soa_serial():
        return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    def update_soa(self):
        record = Record.objects.get(domain=self, type='SOA')
        values = record.content.split()
        if len(values) != 7:
            return
        hostname, email, serial, refresh, retry, expire, default_ttl = values
        serial = self.get_soa_serial()
        Record.objects.filter(pk=record.pk).update(content=' '.join((hostname, email, serial, refresh, retry, expire, default_ttl)))

    def ensure_srv_record(self, protocol, service, port, prio, weight, fqdn):
        name = '_%s._%s' % (service, protocol)
        content = '%s %s %s' % (weight, port, fqdn)
        Record.objects.get_or_create(defaults=self.default_record_values(prio=prio), domain=self, type='SRV', name=name, content=content)

    def ensure_record(self, source, target):
        """
        :param source: orignal name (fqdn of the machine, or IP address)
        :param target: DNS alias to create
        :rtype: :class:`penatesserver.powerdns.models.Domain`
        """
        record_name, sep, domain_name = target.partition('.')
        if sep != '.' or domain_name != self.name:
            return False
        existing_records = list(Record.objects.filter(domain=self, name=record_name, type__in=['A', 'AAAA', 'CNAME']))
        if existing_records:
            Record.objects.filter(domain=self, name=record_name, type__in=['A', 'AAAA', 'CNAME']).update(**self.default_record_values())
            return True
        elif source == target:
            return True
        try:
            add = netaddr.IPAddress(source)
            record_type = 'A' if add.version == 4 else 'AAAA'
        except netaddr.core.AddrFormatError:
            record_type = 'CNAME'
        Record(domain=self, name=record_name, type=record_type, content=source, **self.default_record_values()).save()
        return True


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

    def __repr__(self):
        if self.type in ('NS', 'SOA', 'MX'):
            return 'Record(%s [%s] -> %s)' % (self.name, self.type, self.content)
        return 'Record(%s.%s [%s] -> %s)' % (self.name, self.domain.name, self.type, self.content)

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
