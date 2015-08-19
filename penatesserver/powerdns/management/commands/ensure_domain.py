# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse
from django.core.management import BaseCommand
from penatesserver.models import DhcpSubnet
from penatesserver.powerdns.models import Domain

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('domain', help='Domain name')
        parser.add_argument('--subnet', default=[], action='append', help='Append information to DHCP subnet')

    def handle(self, *args, **options):
        name = options['domain']
        Domain.objects.get_or_create(name=name)
        if options['subnet']:
            for subnet in DhcpSubnet.objects.filter(name__in=options['subnet']):
                subnet.set_option('domain-name', name, replace=True)
                subnet.set_option('nis-domain', name, replace=True)
                subnet.set_option('domain-search', name, replace=True)
                subnet.set_option('dhcp6.domain-search', name, replace=True)
                subnet.set_option('dhcp6.nis-domain-name', name, replace=True)
                subnet.save()
