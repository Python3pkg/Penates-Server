# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.utils.translation import ugettext as _
from penatesserver.glpi.models import ShinkenService

from penatesserver.models import Service
from penatesserver.pki.service import CertificateEntry
from penatesserver.powerdns.models import Domain

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('fqdn', help='Host fqdn')
        parser.add_argument('check_command', help='Nagios check_command')
        parser.add_argument('--description', help='Service description', default=None)
        parser.add_argument('--delete', help='Service description', default=False, action='store_true')

    def handle(self, *args, **options):
        service_description = options['description']
        check_command = options['check_command']
        fqdn = options['fqdn']
        values = {'service_description': service_description}
        if ShinkenService.objects.filter(host_name=fqdn, check_command=check_command)\
                .update(**values) == 0:
            ShinkenService(host_name=fqdn, check_command=check_command, **values).save()
            self.stdout.write(self.style.WARNING('%s:%s created') % (fqdn, check_command))
        elif options['delete']:
            ShinkenService.objects.filter(host_name=fqdn, check_command=check_command).delete()
            self.stdout.write(self.style.ERROR('%s:%s deleted') % (fqdn, check_command))

