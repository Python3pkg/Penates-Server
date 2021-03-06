# -*- coding=utf-8 -*-


import argparse

from django.core.management.base import BaseCommand

from penatesserver.models import Service

__author__ = 'mgallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('fqdn')

    def handle(self, *args, **options):
        fqdn = options['fqdn']
        if Service.objects.filter(fqdn=fqdn).count() == 0:
            self.stdout.write(self.style.WARNING('Service %s unknown') % fqdn)
        else:
            for service in Service.objects.filter(fqdn=fqdn):
                service.delete()
                self.stdout.write(self.style.WARNING('Service %s deleted') % fqdn)
