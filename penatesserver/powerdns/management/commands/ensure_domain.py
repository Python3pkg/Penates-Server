# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import argparse
from django.conf import settings

from django.core.management import BaseCommand

from penatesserver.powerdns.models import Domain

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, argparse.ArgumentParser)
        parser.add_argument('domain', help='Domain name')

    def handle(self, *args, **options):
        name = options['domain']
        for prefix in ('', settings.PDNS_ADMIN_PREFIX, settings.PDNS_CLIENT_PREFIX, settings.PDNS_SERVER_PREFIX):
            Domain.objects.get_or_create(name='%s%s' % (prefix, name, ))
