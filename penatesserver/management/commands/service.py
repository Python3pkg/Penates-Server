# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.utils.translation import ugettext as _

from penatesserver.models import Service
from penatesserver.pki.service import CertificateEntry
from penatesserver.powerdns.models import Domain

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('scheme', help='Service scheme (e.g. http)')
        parser.add_argument('hostname', help='Service hostname (e.g. my_service.test.example.org')
        parser.add_argument('port', help='Service port (e.g. 443)')
        parser.add_argument('--fqdn', default=None, help='Host fqdn (e.g. vm01.test.example.org)')
        parser.add_argument('--kerberos_service', default=None,
                            help='Service name for Kerberos (e.g. HTTP, require --fqdn)')
        parser.add_argument('--srv', default=None, help='SRV DNS field (e.g. tcp/sip:priority:weight, or tcp/sip)')
        parser.add_argument('--protocol', default='tcp', help='Protocol (tcp, udp or socket')
        parser.add_argument('--description', default='', help='Description')
        parser.add_argument('--cert', default=None, help='Destination file for certificate')
        parser.add_argument('--key', default=None, help='Destination file for private key')
        parser.add_argument('--pubkey', default=None, help='Destination file for public key')
        parser.add_argument('--ssh', default=None, help='Destination file for private SSH key')
        parser.add_argument('--pubssh', default=None, help='Destination file for public SSH key')
        parser.add_argument('--ca', default=None, help='Destination file for CA certificate')
        parser.add_argument('--keytab', default=None, help='Destination file for keytab (if --kerberos_service is set)')
        parser.add_argument('--role', default='Service', help='Service type')
        parser.add_argument('--encryption', default='none', help='Encryption level: none, tls or starttls')

    def handle(self, *args, **options):
        # read provided arguments
        kerberos_service = options['kerberos_service']
        fqdn = options['fqdn']
        hostname = options['hostname']
        keytab = options['keytab']
        scheme = options['scheme']
        encryption = options['encryption']
        port = int(options['port'])
        protocol = options['protocol']
        srv_field = options['srv']
        if keytab and not kerberos_service:
            self.stdout.write(self.style.ERROR('--keytab is set without --kerberos_service'))
            return
        if kerberos_service and not fqdn:
            self.stdout.write(self.style.ERROR('--kerberos_service is set without --fqdn'))
            return

        # create service object
        service, created = Service.objects.get_or_create(fqdn=fqdn, scheme=scheme, hostname=hostname, port=port,
                                                         protocol=protocol)
        Service.objects.filter(pk=service.pk).update(kerberos_service=kerberos_service,
                                                     description=options['description'], dns_srv=srv_field,
                                                     encryption=encryption)

        # certificate part
        if options['role']:
            call_command('certificate', hostname, options['role'], organizationName=settings.PENATES_ORGANIZATION,
                         organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                         localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                         stateOrProvinceName=settings.PENATES_STATE, altNames=[],
                         cert=options['cert'], key=options['key'], pubkey=options['pubkey'], ssh=options['ssh'],
                         pubssh=options['pubssh'], ca=options['ca'], initialize=False)
            entry = CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION,
                                     organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                                     localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                                     stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=options['role'])
        else:
            entry = None

        # kerberos part
        if kerberos_service:
            principal = '%s/%s' % (kerberos_service, fqdn)
            call_command('keytab', principal, keytab=keytab)

        # DNS part
        record_name, sep, domain_name = hostname.partition('.')
        if sep == '.':
            domain, created = Domain.objects.get_or_create(name=domain_name)
            domain.ensure_record(fqdn, hostname)
            domain.set_extra_records(scheme, hostname, port, fqdn, srv_field, entry=entry)
            domain.update_soa()
            if entry:
                domain.set_certificate_records(entry, protocol, hostname, port)
