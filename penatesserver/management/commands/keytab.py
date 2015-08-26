# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse
import os

from django.conf import settings

from django.core.management import BaseCommand

from penatesserver.kerb import add_principal_to_keytab, keytab_has_principal, add_principal

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('principal', help='principal name')
        parser.add_argument('--keytab', help='Keytab destination file')

    def handle(self, *args, **options):
        name = '%s@%s' % (options['principal'], settings.PENATES_REALM)
        add_principal(name)
        keytab_filename = options['keytab']
        if not keytab_filename:
            return
        try:
            exists = os.path.exists(keytab_filename)
            with open(keytab_filename, 'ab') as fd:
                fd.write(b'')
            if not exists:
                os.remove(keytab_filename)
            elif keytab_has_principal(name, keytab_filename):
                return
        except OSError as e:
            self.stdout.write(self.style.ERROR('Unable to write file: %s' % keytab_filename))
            raise e
        except ValueError as e:
            self.stdout.write(self.style.ERROR('Invalid keytab file %s' % keytab_filename))
            raise e
        add_principal_to_keytab(name, keytab_filename)
