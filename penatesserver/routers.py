# -*- coding: utf-8 -*-
from __future__ import unicode_literals
__author__ = 'Matthieu Gallet'


# noinspection PyMethodMayBeStatic,PyProtectedMember,PyUnusedLocal
class PowerdnsManagerDbRouter(object):

    def db_for_read(self, model, **hints):
        """Point all operations on powerdns models to 'powerdns'"""
        if model._meta.app_label == 'powerdns':
            return 'powerdns'
        return None

    def db_for_write(self, model, **hints):
        """Point all operations on powerdns models to 'powerdns'"""
        if model._meta.app_label == 'auth':
            return 'default'
        elif model._meta.app_label == 'powerdns':
            return 'powerdns'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow any relation if a model in powerdns is involved"""
        if obj1._meta.app_label == 'powerdns' or obj2._meta.app_label == 'powerdns':
            return True
        return None

    def allow_migrate(self, db, model):
        """Make sure the powerdns app only appears on the 'powerdns' db"""
        if db == 'powerdns':
            return model._meta.app_label == 'powerdns'
        elif model._meta.app_label == 'powerdns':
            return False
        return None
