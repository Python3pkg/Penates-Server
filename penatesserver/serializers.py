# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.utils import html
from django.utils.translation import ugettext as _
from penatesserver.models import User, Group, name_validators

__author__ = 'Matthieu Gallet'


class UserSerializer(serializers.Serializer):
    name = serializers.CharField(validators=list(name_validators))
    display_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    uid_number = serializers.IntegerField(required=False, read_only=True, allow_null=True)
    gid_number = serializers.IntegerField(required=False, allow_null=True, label=_('GID number'))
    phone = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def create(self, validated_data):
        if User.objects.filter(name=validated_data['name']).count() > 0:
            raise ValueError
        elif validated_data.get('uid_number') and User.objects.filter(uid_number=validated_data['uid_number']).count() > 0:
            raise ValueError
        user = User(**validated_data)
        user.save()
        return user

    def update(self, instance, validated_data):
        assert isinstance(instance, User)
        for attr_name in ('display_name', 'gid_number', 'phone'):
            if attr_name in validated_data:
                setattr(instance, attr_name, validated_data[attr_name])
        instance.save()
        return instance


class JsonListField(serializers.ListField):
    def get_value(self, dictionary):
        if html.is_html_input(dictionary):
            content = dictionary.get(self.field_name, [''])
            return [x.strip() for x in content.splitlines() if x.strip()]
        return dictionary.get(self.field_name, [])


class GroupSerializer(serializers.Serializer):
    name = serializers.CharField(validators=list(name_validators), label=_('Name'))
    gid = serializers.IntegerField(required=False, allow_null=True, label=_('GID'))
    members = JsonListField(required=False, child=serializers.CharField(validators=list(name_validators)), label=_('Members'))

    def create(self, validated_data):
        if Group.objects.filter(name=validated_data['name']).count() > 0:
            raise ValueError
        elif validated_data.get('gid') and Group.objects.filter(gid=validated_data['gid']).count() > 0:
            raise ValueError
        validated_data['members'] = self.check_members([], validated_data)
        user = Group(**validated_data)
        user.save()
        return user

    def update(self, instance, validated_data):
        assert isinstance(instance, Group)
        members = self.check_members(instance.members, validated_data)
        instance.members = members
        instance.save()
        return instance

    @staticmethod
    def check_members(default_members, validated_data):
        if 'members' in validated_data:
            members = list(set(validated_data['members'] or []))
            if members and User.objects.filter(name__in=members).count() < len(members):
                raise ValueError
        else:
            members = default_members
        return members
