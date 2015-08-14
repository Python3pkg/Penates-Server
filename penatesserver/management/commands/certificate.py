# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse
import os
from django.core.management import BaseCommand
from penatesserver.pki.constants import ROLES, ALT_TYPES
from penatesserver.pki.service import CertificateEntry, PKI

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('commonName')
        parser.add_argument('role')
        parser.add_argument('--organizationName', default='')
        parser.add_argument('--organizationalUnitName', default='')
        parser.add_argument('--emailAddress', default='')
        parser.add_argument('--localityName', default='')
        parser.add_argument('--countryName', default='FR')
        parser.add_argument('--stateOrProvinceName', default='')
        parser.add_argument('--altNames', default=[], action='append')
        parser.add_argument('--cert', default=None, help='Destination file for certificate')
        parser.add_argument('--key', default=None, help='Destination file for private key')
        parser.add_argument('--pubkey', default=None, help='Destination file for public key')
        parser.add_argument('--ssh', default=None, help='Destination file for private SSH key')
        parser.add_argument('--pubssh', default=None, help='Destination file for public SSH key')
        parser.add_argument('--ca', default=None, help='Destination file for CA certificate')
        parser.add_argument('--initialize', default=False, action='store_true', help='Create a root CA')

    def handle(self, *args, **options):
        role = options['role']
        if role not in ROLES:
            self.stdout.write(self.style.ERROR('Invalid role: %s' % role))
            self.stdout.write('Valid roles: %s' % ', '.join(ROLES))
            return
        alt_names = []
        for alt_name in options['altNames']:
            kind, sep, value = alt_name.partition(':')
            if sep != ':' or kind not in dict(ALT_TYPES):
                self.stdout.write(self.style.ERROR('Altname %s must be of form KIND:VALUE with KIND one of %s' % (alt_name, ', '.join(ALT_TYPES))))
                return
            alt_names.append((kind, value))
        for key in 'cert', 'key', 'ssh', 'ca', 'pubssh', 'pubkey':
            if not options[key]:
                continue
            try:
                with open(options[key], 'wb') as fd:
                    fd.write(b'')
            except OSError:
                self.stdout.write(self.style.ERROR('Unable to write file: %s' % options[key]))
                return
        entry = CertificateEntry(options['commonName'],
                                 organizationalUnitName=options['organizationalUnitName'],
                                 emailAddress=options['emailAddress'],
                                 localityName=options['localityName'],
                                 countryName=options['countryName'],
                                 stateOrProvinceName=options['stateOrProvinceName'],
                                 altNames=alt_names,
                                 role=role)
        pki = PKI()
        pki.initialize()
        if options['initialize']:
            pki.ensure_ca(entry)
        else:
            pki.ensure_certificate(entry)

        for key, attr in (('cert', 'crt_filename'), ('key', 'key_filename'), ('ssh', 'key_filename'),
                          ('ca', 'ca_filename'), ('pubssh', 'ssh_filename'), ('pubkey', 'pub_filename'), ):
            dst_filename = options[key]
            if not dst_filename:
                continue
            src_filename = getattr(entry, attr)
            open(dst_filename, 'ab').write(open(src_filename, 'rb').read())
            self.stdout.write('File %s written' % dst_filename)
