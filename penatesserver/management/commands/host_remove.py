# -*- coding=utf-8 -*-
from __future__ import unicode_literals
import argparse
from django.core.management.base import BaseCommand
from penatesserver.models import Host

__author__ = 'mgallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('fqdn')

    def handle(self, *args, **options):
        fqdn = options['fqdn']
        if Host.objects.filter(fqdn=fqdn).count() == 0:
            self.stdout.write(self.style.WARNING('Host %s unknown') % fqdn)
        else:
            for host in Host.objects.filter(fqdn=fqdn):
                host.delete()
                self.stdout.write(self.style.WARNING('Host %s deleted') % fqdn)
