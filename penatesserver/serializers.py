# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework.serializers import ModelSerializer
from penatesserver.models import User, Group

__author__ = 'Matthieu Gallet'


class UserSerializer(ModelSerializer):
    class Meta(object):
        model = User
        fields = ('name', 'display_name', 'uid_number', 'gid_number', 'jpeg_photo', 'phone', )


class GroupSerializer(ModelSerializer):
    class Meta(object):
        model = Group
        fields = ('name', 'gid', )
