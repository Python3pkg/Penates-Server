# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse
import re

from django.conf import settings
from django.core.management import BaseCommand, call_command

from django.utils.translation import ugettext as _
import netaddr

from penatesserver.models import Service
from penatesserver.powerdns.models import Record, Domain

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('protocol', help='Service protocol (e.g. http)')
        parser.add_argument('hostname', help='Service hostname')
        parser.add_argument('port', help='Service port (e.g. 443)')
        parser.add_argument('--fqdn', default=None, help='Host fqdn')
        parser.add_argument('--kerberos_service', default=None, help='Service name for Kerberos (e.g. HTTP, require --fqdn)')
        parser.add_argument('--srv', default=None, help='SRV DNS field (e.g. tcp/sip:priority:weight, or tcp/sip)')
        parser.add_argument('--description', default='', help='Description')
        parser.add_argument('--cert', default=None, help='Destination file for certificate')
        parser.add_argument('--key', default=None, help='Destination file for private key')
        parser.add_argument('--pubkey', default=None, help='Destination file for public key')
        parser.add_argument('--ssh', default=None, help='Destination file for private SSH key')
        parser.add_argument('--pubssh', default=None, help='Destination file for public SSH key')
        parser.add_argument('--ca', default=None, help='Destination file for CA certificate')
        parser.add_argument('--keytab', default=None, help='Destination file for keytab (if --kerberos_service is set)')
        parser.add_argument('--role', default='Service', help='Service type')

    def handle(self, *args, **options):
        kerberos_service = options['kerberos_service']
        fqdn = options['fqdn']
        hostname = options['hostname']
        keytab = options['keytab']
        if keytab and not kerberos_service:
            self.stdout.write(self.style.ERROR('--keytab is set without --kerberos_service'))
            return
        if kerberos_service and not fqdn:
            self.stdout.write(self.style.ERROR('--kerberos_service is set without --fqdn'))
            return
        protocol = options['protocol']
        port = int(options['port'])
        service, created = Service.objects.get_or_create(fqdn=fqdn, protocol=protocol, hostname=hostname, port=port)
        srv_field = options['srv']
        Service.objects.filter(pk=service.pk).update(kerberos_service=kerberos_service, description=options['description'], dns_srv=srv_field)
        call_command('certificate', hostname, options['role'], organizationName=settings.PENATES_ORGANIZATION,
                     organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                     localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                     stateOrProvinceName=settings.PENATES_STATE, altNames=[],
                     cert=options['cert'], key=options['key'], pubkey=options['pubkey'], ssh=options['ssh'],
                     pubssh=options['pubssh'], ca=options['ca'], initialize=False, )
        domain = self.ensure_record(fqdn, hostname)
        if kerberos_service:
            principal = '%s/%s' % (kerberos_service, fqdn)
            call_command('keytab', principal, keytab=keytab)
        if protocol == 'dns':
            Record.objects.get_or_create(defaults={'ttl': 86400, 'prio': 0}, domain=domain, record_type='NS', name=domain.name, content=hostname)
            if Record.objects.filter(domain=domain, record_type='SOA').count() == 0:
                content = '%s %s 1 10800 3600 604800 3600' % (hostname, settings.PENATES_EMAIL_ADDRESS)
                Record.objects.get_or_create(defaults={'ttl': 86400, 'prio': 0}, domain=domain, record_type='SOA', name=domain.name, content=content)
        if protocol == 'smtp':
            content = '10 %s' % hostname
            Record.objects.get_or_create(defaults={'ttl': 86400, 'prio': 0}, domain=domain, record_type='MX', name=domain.name, content=content)
        if srv_field:
            matcher = re.match(r'^(\w+)/(\w+):(\d+):(\d+)$', srv_field)
            if matcher:
                name = '_%s._%s' % (matcher.group(2), matcher.group(1))
                content = '%s %s %s' % (matcher.group(4), port, fqdn)
                prio = int(matcher.group(3))
                Record.objects.get_or_create(defaults={'ttl': 86400, 'prio': prio, }, domain=domain, record_type='SRV', name=name, content=content)
            matcher = re.match(r'^(\w+)/(\w+)$', srv_field)
            if matcher:
                name = '_%s._%s' % (matcher.group(2), matcher.group(1))
                content = '100 %s %s' % (port, fqdn)
                Record.objects.get_or_create(defaults={'ttl': 86400, 'prio': 0, }, domain=domain, record_type='SRV', name=name, content=content)

    @staticmethod
    def ensure_record(source, target):
        """
        :param source: orignal name (fqdn of the machine, or IP address)
        :param target: DNS alias to create
        :rtype: :class:`penatesserver.powerdns.models.Domain`
        """
        if source == target:
            return True
        record_name, sep, domain_name = target.partition('.')
        if sep != '.':
            return False
        domain, created = Domain.objects.get_or_create(name=domain_name)
        if Record.objects.filter(domain=domain, name=record_name, type__in=['A', 'AAAA', 'CNAME']).count() > 0:
            return True
        try:
            add = netaddr.IPAddress(source)
            record_type = 'A' if add.version == 4 else 'AAAA'
        except netaddr.core.AddrFormatError:
            record_type = 'CNAME'
        record = Record(domain=domain, name=record_name, type=record_type, content=source, ttl=3600, prio=0)
        record.save()
        return domain
