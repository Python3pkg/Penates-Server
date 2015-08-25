# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url

from rest_framework import routers

from penatesserver.models import name_pattern
from penatesserver.views import GroupDetail, GroupList, UserDetail, UserList

__author__ = 'flanker'

router = routers.DefaultRouter()

service_pattern = r'(?P<scheme>\w+)/(?P<hostname>[a-zA-Z0-9\.\-_]+)/(?P<port>\d+)/'

urls = [
    ('^index$', 'penatesserver.views.index'),
    url(r'^', include(router.urls)),
    url(r'^no-auth/get_host_keytab/(?P<hostname>[a-zA-Z0-9\.\-_]+)$', 'penatesserver.views.get_host_keytab'),
    url(r'^auth/get_info/$', 'penatesserver.views.get_info'),
    url(r'^auth/set_dhcp/(?P<mac_address>([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})/$', 'penatesserver.views.set_dhcp'),
    url(r'^auth/conf/dhcpd.conf$', 'penatesserver.views.get_dhcpd_conf'),
    url(r'^auth/get_host_certificate/$', 'penatesserver.views.get_host_certificate'),
    url(r'^auth/set_ssh_pub/$', 'penatesserver.views.set_ssh_pub'),
    url(r'^auth/set_service/%s$' % service_pattern, 'penatesserver.views.set_service'),
    url(r'^auth/set_extra_service/(?P<hostname>[a-zA-Z0-9\.\-_]+)$', 'penatesserver.views.set_extra_service'),
    url(r'^auth/get_service_keytab/%s$' % service_pattern, 'penatesserver.views.get_service_keytab'),
    url(r'^auth/get_service_certificate/%s$' % service_pattern, 'penatesserver.views.get_service_certificate'),
    url(r'^auth/user/$', UserList.as_view(), name='user_list'),
    url(r'^auth/user/(?P<name>%s)$' % name_pattern, UserDetail.as_view(), name='user_detail'),
    url(r'^auth/group/$', GroupList.as_view(), name='group_list'),
    url(r'^auth/group/(?P<name>%s)$' % name_pattern, GroupDetail.as_view(), name='group_detail'),
    url(r'^auth/change_password/$', 'penatesserver.views.change_own_password'),
    url(r'^auth/get_user_certificate/$', 'penatesserver.views.get_user_certificate'),
    url(r'^auth/get_email_certificate/$', 'penatesserver.views.get_email_certificate'),
    url(r'^auth/get_signature_certificate/$', 'penatesserver.views.get_signature_certificate'),
    url(r'^auth/get_encipherment_certificate/$', 'penatesserver.views.get_encipherment_certificate'),
    url(r'^auth/api/', include('rest_framework.urls', namespace='rest_framework'))
]
