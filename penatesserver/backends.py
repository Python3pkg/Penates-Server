# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import Group
from penatesserver.utils import is_admin

__author__ = 'Matthieu Gallet'


CACHED_GROUPS = {}


class DefaultGroupRemoteUserBackend(RemoteUserBackend):

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified; only add it to the default group.
        """
        user.is_staff = is_admin(user.username)
        user.is_active = True
        user.is_superuser = is_admin(user.username)
        user.save()
        group_name = settings.FLOOR_DEFAULT_GROUP_NAME
        if group_name is None:
            return user
        if group_name not in CACHED_GROUPS:
            CACHED_GROUPS[group_name] = Group.objects.get_or_create(name=str(group_name))[0]
        user.groups.add(CACHED_GROUPS[group_name])
        return user
