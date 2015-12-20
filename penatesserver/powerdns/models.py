# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import datetime
import re
import time
from django.conf import settings
from django.utils.six import text_type
import netaddr
from penatesserver.pki.service import CertificateEntry
from django.db import models
from penatesserver.subnets import get_subnets

__author__ = 'Matthieu Gallet'


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

    def set_extra_records(self, scheme, hostname, port, fqdn, srv_field, entry=None):
        if scheme == 'dns':
            soa_serial = self.get_soa_serial()
            for domain in Domain.objects.filter(name__in=[self.name, '%s%s' % (settings.PDNS_ADMIN_PREFIX, self.name),
                                                          '%s%s' % (settings.PDNS_INFRA_PREFIX, self.name)]):
                Record.objects.get_or_create(domain=domain, type='NS', name=domain.name, content=hostname)
                if Record.objects.filter(domain=domain, type='SOA').count() == 0:
                    content = '%s %s %s 10800 3600 604800 3600' % (hostname, settings.PENATES_EMAIL_ADDRESS, soa_serial)
                    Record.objects.get_or_create(domain=domain, type='SOA', name=domain.name, content=content)
        elif scheme == 'smtp' and port == 25:
            Record.objects.get_or_create(defaults={'prio': 10}, domain=self, type='MX', name=self.name, content=hostname)
            content = 'v=spf1 mx mx:%s -all' % self.name
            if Record.objects.filter(domain=self, type='TXT', name=self.name, content__startswith='v=spf1').update(content=content) == 0:
                Record(domain=self, type='TXT', name=self.name, content=content).save()
        elif scheme == 'dkim' and entry is not None:
            assert isinstance(entry, CertificateEntry)
            with codecs.open(entry.pub_filename, 'r', encoding='utf-8') as fd:
                content = fd.read()
            content = 'v=DKIM1; k=rsa; p=' + content.replace('-----END PUBLIC KEY-----', '').replace('-----BEGIN PUBLIC KEY-----', '').strip()
            name = '%s._domainkey.%s' % (hostname.partition('.')[0], self.name)
            if Record.objects.filter(domain=self, type='TXT', name=name, content__startswith='v=DKIM1;').update(content=content) == 0:
                Record(domain=self, type='TXT', name=name, content=content).save()
            content = 't=n;o=-;r=postmaster@%s' % self.name
            name = '_domainkey.%s' % self.name
            if Record.objects.filter(domain=self, type='TXT', name=name, content=content).count() == 0:
                Record(domain=self, type='TXT', name=name, content=content).save()
        if srv_field:
            matcher_full = re.match(r'^(\w+)/([\-\w]+):(\d+):(\d+)$', srv_field)
            matcher_protocol = re.match(r'^([\-\w]+)/(\w+)$', srv_field)
            matcher_service = re.match(r'^([\-\w]+)$', srv_field)
            if matcher_full:
                self.ensure_srv_record(matcher_full.group(1), matcher_full.group(2), port, int(matcher_full.group(3)), int(matcher_full.group(4)), fqdn)
            elif matcher_protocol:
                self.ensure_srv_record(matcher_protocol.group(1), matcher_protocol.group(2), port, 0, 100, fqdn)
            elif matcher_service:
                self.ensure_srv_record('tcp', matcher_service.group(1), port, 0, 100, fqdn)

    def set_certificate_records(self, entry, protocol, hostname, port):
        record_name = '_%s.%s' % (protocol, hostname)
        Record.objects.get_or_create(name=record_name, domain=self)
        record_name = '_%d._%s.%s' % (port, protocol, hostname)
        content = '3 0 1 %s' % entry.crt_sha256
        if Record.objects.filter(name=record_name, domain=self, type='TLSA').update(content=content) == 0:
            Record(name=record_name, domain=self, type='TLSA', content=content).save()

    @staticmethod
    def get_soa_serial():
        return datetime.datetime.now().strftime(text_type('%Y%m%d%H'))

    def update_soa(self):
        records = list(Record.objects.filter(domain=self, type='SOA')[0:1])
        if not records:
            return False
        record = records[0]
        values = record.content.split()
        if len(values) != 7:
            return False
        hostname, email, serial, refresh, retry, expire, default_ttl = values
        serial = self.get_soa_serial()
        Record.objects.filter(pk=record.pk).update(content=' '.join((hostname, email, serial, refresh, retry, expire, default_ttl)))
        return True

    def ensure_srv_record(self, protocol, service, port, prio, weight, fqdn):
        name = '_%s.%s' % (protocol, self.name)
        Record.objects.get_or_create(defaults={'prio': None}, domain=self, type=None, name=name, content=None)
        name = '_%s._%s.%s' % (service, protocol, self.name)
        content = '%s %s %s' % (weight, port, fqdn)
        Record.objects.get_or_create(defaults={'prio': prio}, domain=self, type='SRV', name=name, content=content)

    @staticmethod
    def ensure_auto_record(source, target, unique=False, override_reverse=False):
        base, sep, domain_name = target.partition('.')
        domain = Domain.objects.get(name=domain_name)
        domain.ensure_record(source, target, unique=unique, override_reverse=override_reverse)
        domain.update_soa()

    def ensure_record(self, source, target, unique=False, override_reverse=True):
        """
        :param source: orignal name (fqdn of the machine, or IP address)
        :param target: DNS alias to create
        :param unique: if True, remove any previous
        :rtype: :class:`penatesserver.powerdns.models.Domain`
        """
        record_name, sep, domain_name = target.partition('.')
        if sep != '.' or domain_name != self.name:
            return False
        if source == target:
            return True
        try:
            add = netaddr.IPAddress(source)
            record_type = 'A' if add.version == 4 else 'AAAA'
        except netaddr.core.AddrFormatError:
            record_type = 'CNAME'
            add = None
        if not unique and Record.objects.filter(domain=self, name=target, type=record_type, content=source).count() > 0:
            return True
        if record_type == 'A' or record_type == 'AAAA':
            for subnet_obj in get_subnets():
                if add.version != subnet_obj.network.version or add not in subnet_obj.network:
                    continue
                reverse_record_name, sep, reverse_domain_name = add.reverse_dns.partition('.')
                reverse_domain_name = reverse_domain_name[:-1]
                reverse_target = add.reverse_dns[:-1]
                reverse_domain = self.ensure_subdomain(reverse_domain_name)
                query = Record.objects.filter(domain=reverse_domain, name=reverse_target, type='PTR')
                if (override_reverse and query.update(content=target) == 0) or (not override_reverse and query.count() == 0):
                    Record(domain=reverse_domain, name=reverse_target, type='PTR', content=target, ttl=3600).save()
                    assert isinstance(reverse_domain, Domain)
                    reverse_domain.update_soa()
        if Record.objects.filter(domain=self, name=target, type__in=['A', 'AAAA', 'CNAME'])\
                .update(type=record_type, content=source, ttl=3600) == 0:
            Record(domain=self, name=target, type=record_type, content=source, ttl=3600).save()
        return True

    def ensure_subdomain(self, subdomain_name):
        subdomain, created = Domain.objects.get_or_create(name=subdomain_name)
        Record.objects.get_or_create(defaults={'prio': None}, domain=self, type=None, name=subdomain_name, content=None)
        if Record.objects.filter(domain=subdomain, type='SOA').count() == 0:
            soa_records = list(Record.objects.filter(domain=self, type='SOA')[0:1])
            if soa_records:
                Record(domain=subdomain, type='SOA', name=subdomain_name, content=soa_records[0].content).save()
        return subdomain

    def __repr__(self):
        return "Domain('%s')" % self.name


class Record(models.Model):
    domain = models.ForeignKey(Domain, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=10, blank=True, null=True)
    content = models.CharField(max_length=65535, blank=True, null=True)
    ttl = models.IntegerField(blank=True, null=True, default=86400)
    prio = models.IntegerField(blank=True, null=True, default=0)
    change_date = models.IntegerField(blank=True, null=True, default=time.time)
    disabled = models.NullBooleanField(default=False)
    ordername = models.CharField(max_length=255, blank=True, null=True)
    auth = models.NullBooleanField(default=True)

    def __repr__(self):
        if self.type in ('NS', 'SOA', 'MX'):
            return 'Record("%s [%s] -> %s")' % (self.name, self.type, self.content)
        return 'Record("%s [%s] -> %s")' % (self.name, self.type, self.content)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        domain_name = self.domain.name
        # noinspection PyTypeChecker
        self.auth = self.name.endswith(domain_name)
        if self.auth:
            comp = self.name[:-(1 + len(domain_name))].split(text_type('.'))
            comp.reverse()
            self.ordername = ' '.join(comp)
        super(Record, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    class Meta(object):
        managed = False
        db_table = 'records'

    @staticmethod
    def local_resolve(name, searched_types=None):
        """ Try to locally resolve a name to A or AAAA record
        :param name:
        :type name:
        :rtype: basestring
        """
        if searched_types is None:
            searched_types = ['A', 'AAAA', 'CNAME']
        try:
            netaddr.IPAddress(name)
            return name
        except netaddr.core.AddrFormatError:
            pass
        to_check = [name]
        excluded = set()
        while to_check:
            new_to_check = []
            for record_data in Record.objects.filter(name__in=to_check, type__in=searched_types).values_list('type', 'content'):
                if record_data[0] == 'A' or record_data[0] == 'AAAA':
                    return record_data[1]
                elif record_data[1] not in excluded:
                    new_to_check.append(record_data[1])
                excluded.add(record_data[1])
            searched_types = ['A', 'AAAA', 'CNAME']
            to_check = new_to_check
        return None


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
