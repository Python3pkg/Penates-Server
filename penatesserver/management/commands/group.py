# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from argparse import ArgumentParser

from django.core.management import BaseCommand

from penatesserver.models import Group
from penatesserver.utils import force_bytestring

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('groupname')
        parser.add_argument('--gid', default=None)

    def handle(self, *args, **options):
        groupname = options['groupname']
        if not list(Group.objects.filter(name=force_bytestring(groupname))[0:1]):
            group = Group(name=groupname, gid=options['gid'])
            group.save()
