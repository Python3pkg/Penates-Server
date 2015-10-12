# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from argparse import ArgumentParser
from django.core.management import BaseCommand
from penatesserver.models import User, Group

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('username')
        parser.add_argument('--uid', default=None)
        parser.add_argument('--gid', default=None)
        parser.add_argument('--display_name', default=None)
        parser.add_argument('--phone', default=None)
        parser.add_argument('--password', default=None)
        parser.add_argument('--group', default=[], action='append')

    def handle(self, *args, **options):

        username = options['username']
        users = list(User.objects.filter(name=username)[0:1])
        if not users:
            user = User(name=username, uid_number=options['uid'], gid_number=options['gid'])
        else:
            user = users[0]
        if options['display_name']:
            user.display_name = options['display_name']
        if options['phone']:
            user.phone = options['phone']
        if options['gid']:
            user.gid = options['gid']
        if options['password']:
            user.set_password(options['password'])
        else:
            user.save()
        for group_name in options['group']:
            groups = list(Group.objects.filter(name=group_name)[0:1])
            if groups:
                group = groups[0]
            else:
                group = Group(name=group_name)
            if username not in group.members:
                group.members.append(username)
            group.save()
