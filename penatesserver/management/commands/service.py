# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse

from django.conf import settings
from django.core.management import BaseCommand
from django.utils.translation import ugettext as _

from penatesserver.models import Service
from penatesserver.management.commands.certificate import Command as CertificateCommand
from penatesserver.management.commands.keytab import Command as KeytabCommand

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('protocol', help='Service protocol (e.g. http)')
        parser.add_argument('hostname', help='Service hostname')
        parser.add_argument('port', help='Service port (e.g. 443)')
        parser.add_argument('--fqdn', default=None, help='Host fqdn')
        parser.add_argument('--kerberos_service', default=None, help='Service name for Kerberos (e.g. HTTP, require --fqdn)')
        parser.add_argument('--description', default='', help='Description')
        parser.add_argument('--cert', default=None, help='Destination file for certificate')
        parser.add_argument('--key', default=None, help='Destination file for private key')
        parser.add_argument('--pubkey', default=None, help='Destination file for public key')
        parser.add_argument('--ssh', default=None, help='Destination file for private SSH key')
        parser.add_argument('--pubssh', default=None, help='Destination file for public SSH key')
        parser.add_argument('--ca', default=None, help='Destination file for CA certificate')
        parser.add_argument('--keytab', default=None, help='Destination file for keytab (if --kerberos_service is set)')

    def handle(self, *args, **options):
        if options['keytab'] and not options['kerberos_service']:
            self.stdout.write(self.style.ERROR('--keytab is set without --kerberos_service'))
            return
        if options['kerberos_service'] and not options['fqdn']:
            self.stdout.write(self.style.ERROR('--kerberos_service is set without --fqdn'))
            return
        key = 'keytab'
        if options[key]:
            try:
                with open(options[key], 'wb') as fd:
                    fd.write(b'')
            except OSError:
                self.stdout.write(self.style.ERROR('Unable to write file: %s' % options[key]))
                return
        service, created = Service.objects.get_or_create(fqdn=options['fqdn'],
                                                         protocol=options['protocol'],
                                                         hostname=options['hostname'],
                                                         port=options['port'])
        Service.objects.filter(pk=service.pk).update(kerberos_service=options['kerberos_service'],
                                                     description=options['description'])
        cert_command = CertificateCommand()
        cert_command.handle(commonName=options['hostname'], role='Service', organizationName=settings.PENATES_ORGANIZATION,
                            organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                            localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                            stateOrProvinceName=settings.PENATES_STATE, altNames=[],
                            cert=options['cert'], key=options['key'], pubkey=options['pubkey'], ssh=options['ssh'],
                            pubssh=options['pubssh'], ca=options['ca'], initialize=False, )
        keytab_command = KeytabCommand()
        if options['kerberos_service']:
            principal = '%s/%s' % (options['kerberos_service'], options['fqdn'])
            keytab_command.handle(principal=principal, keytab=options['keytab'])
