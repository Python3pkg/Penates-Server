# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse
import os
from django.conf import settings
from django.core.management import BaseCommand
import subprocess
from penatesserver.models import Principal

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('principal', help='principal name')
        parser.add_argument('--keytab', help='Keytab destination file')

    def handle(self, *args, **options):
        name = '%s@%s' % (options['principal'], settings.PENATES_REALM)
        if not list(Principal.objects.filter(name=name)[0:1]):
            Principal(name=name).save()
        keytab_filename = options['keytab']
        if keytab_filename:
            try:
                exists = os.path.exists(keytab_filename)
                with open(keytab_filename, 'ab') as fd:
                    fd.write(b'')
                if not exists:
                    os.remove(keytab_filename)
            except OSError:
                self.stdout.write(self.style.ERROR('Unable to write file: %s' % keytab_filename))
                return
            p = subprocess.Popen(['kadmin', '-p', settings.PENATES_PRINCIPAL, '-k', '-t', settings.PENATES_KEYTAB, '-q', 'ktadd -k %s %s' % (keytab_filename, name)])
            p.communicate()
