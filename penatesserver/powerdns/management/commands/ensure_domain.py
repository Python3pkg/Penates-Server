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
        domain, created = Domain.objects.get_or_create(name=name)
        domain.ensure_subdomain('%s%s' % (settings.PDNS_ADMIN_PREFIX, name))
        domain.ensure_subdomain('%s%s' % (settings.PDNS_INFRA_PREFIX, name))
