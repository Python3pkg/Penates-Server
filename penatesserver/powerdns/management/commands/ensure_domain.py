# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse
from django.core.management import BaseCommand
from penatesserver.powerdns.models import Domain

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('domain', help='Domain name')

    def handle(self, *args, **options):
        name = options['domain']
        Domain.objects.get_or_create(defaults=Domain.default_domain_values(type='NATIVE'), name=name)
