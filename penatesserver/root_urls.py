# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf.urls import include, url
from rest_framework import routers

__author__ = 'flanker'

router = routers.DefaultRouter()

urls = [
    ('^index$', 'penatesserver.views.index'),
    url(r'^', include(router.urls)),
    url(r'^no-auth/get_host_keytab/(?P<hostname>[a-zA-Z0-9\.\-_]+)$', 'penatesserver.views.get_host_keytab'),
    url(r'^auth/get_info/', 'penatesserver.views.get_info'),
    url(r'^auth/get_host_certificate/', 'penatesserver.views.get_host_certificate'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    
]
