# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from argparse import ArgumentParser

from django.contrib.auth.models import Permission
from django.core.management import BaseCommand
from django.utils.encoding import force_text

from penatesserver.models import AdminUser

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('username')
        parser.add_argument('--password', default=None)
        parser.add_argument('--permission', default=[], action='append')

    def handle(self, *args, **options):
        username = force_text(options['username'])
        users = list(AdminUser.objects.filter(username=username)[0:1])
        if not users:
            user = AdminUser(username=username)
        else:
            user = users[0]
        if options['password']:
            user.set_password(force_text(options['password']))
        user.save()
        permissions = list(Permission.objects.filter(codename__in=[force_text(x) for x in options['permission']]))
        user.user_permissions.add(*permissions)
