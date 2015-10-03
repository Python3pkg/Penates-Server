# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.test.runner import DiscoverRunner

__author__ = 'Matthieu Gallet'


class ManagedModelTestRunner(DiscoverRunner):
    """
    Test runner that automatically makes all unmanaged models in your Django
    project managed for the duration of the test run, so that one doesn't need
    to execute the SQL manually to create them.
    """
    def setup_test_environment(self, **kwargs):
        try:
            # noinspection PyUnresolvedReferences
            from django.apps import apps
            get_models = apps.get_models
        except ImportError:
            from django.db.models.loading import get_models
        # noinspection PyAttributeOutsideInit,PyProtectedMember
        self.unmanaged_models = [m for m in get_models() if not m._meta.managed]
        for m in self.unmanaged_models:
            # noinspection PyProtectedMember
            m._meta.managed = True
        settings.RUNNING_TESTS = True
        super(ManagedModelTestRunner, self).setup_test_environment(**kwargs)

    def teardown_test_environment2(self, **kwargs):
        super(ManagedModelTestRunner, self).teardown_test_environment(**kwargs)
        # reset unmanaged models
        for m in self.unmanaged_models:
            # noinspection PyProtectedMember
            m._meta.managed = False
