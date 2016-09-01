# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse

from django.conf import settings
from django.core.management import BaseCommand

from penatesserver.models import Host
from penatesserver.utils import register_host, register_mac_address

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('fqdn')
        parser.add_argument('--owner', default=None)
        parser.add_argument('--main_ip_address', default=None)
        parser.add_argument('--main_mac_address', default=None)
        parser.add_argument('--admin_ip_address', default=None)
        parser.add_argument('--admin_mac_address', default=None)
        parser.add_argument('--serial', default=None)
        parser.add_argument('--model_name', default=None)
        parser.add_argument('--location', default=None)
        parser.add_argument('--os_name', default=None)
        parser.add_argument('--bootp_filename', default=None)
        parser.add_argument('--proc_model', default=None)
        parser.add_argument('--proc_count', default=None)
        parser.add_argument('--core_count', default=None)
        parser.add_argument('--memory_size', default=None)
        parser.add_argument('--disk_size', default=None)

    def handle(self, *args, **options):
        fqdn = options['fqdn']
        short_hostname = fqdn.partition('.')[0]
        fqdn = '%s.%s%s' % (short_hostname, settings.PDNS_INFRA_PREFIX, settings.PENATES_DOMAIN)
        new_host = Host.objects.filter(fqdn=fqdn).count() == 0
        keys = {'owner', 'main_ip_address', 'main_mac_address', 'admin_ip_address', 'admin_mac_address', 'serial',
                'model_name', 'location', 'os_name', 'bootp_filename', 'proc_model', 'proc_count', 'core_count',
                'memory_size', 'disk_size', }
        values = {key: options[key] for key in keys if options[key]}
        register_host(short_hostname, main_ip_address=options['main_ip_address'],
                      admin_ip_address=options['admin_ip_address'])
        register_mac_address(fqdn, options['main_ip_address'], options['main_mac_address'],
                             options['admin_ip_address'], options['admin_mac_address'])
        Host.objects.filter(fqdn=fqdn).update(**values) == 0
        if new_host:
            self.stdout.write(self.style.WARNING('Host %s created') % fqdn)
        else:
            self.stdout.write(self.style.WARNING('Host %s updated') % fqdn)
