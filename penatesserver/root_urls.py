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
    url(r'^auth/set_mount_point/$', 'penatesserver.views.set_mount_point'),
    url(r'^auth/set_ssh_pub/$', 'penatesserver.views.set_ssh_pub'),
    url(r'^auth/set_service/%s$' % service_pattern, 'penatesserver.views.set_service'),
    url(r'^auth/set_extra_service/(?P<hostname>[a-zA-Z0-9\.\-_]+)$', 'penatesserver.views.set_extra_service'),
    url(r'^auth/get_service_keytab/%s$' % service_pattern, 'penatesserver.views.get_service_keytab'),
    url(r'^auth/user/$', UserList.as_view(), name='user_list'),
    url(r'^auth/user/(?P<name>%s)$' % name_pattern, UserDetail.as_view(), name='user_detail'),
    url(r'^auth/group/$', GroupList.as_view(), name='group_list'),
    url(r'^auth/group/(?P<name>%s)$' % name_pattern, GroupDetail.as_view(), name='group_detail'),
    url(r'^auth/change_password/$', 'penatesserver.views.change_own_password'),
    url(r'^auth/get_host_certificate/$', 'penatesserver.pki.views.get_host_certificate'),
    url(r'^auth/get_admin_certificate/$', 'penatesserver.pki.views.get_admin_certificate'),
    url(r'^auth/get_service_certificate/%s$' % service_pattern, 'penatesserver.pki.views.get_service_certificate'),
    url(r'^no-auth/(?P<kind>ca|users|hosts|services).pem$', 'penatesserver.pki.views.get_ca_certificate'),
    url(r'^no-auth/crl.pem$', 'penatesserver.pki.views.get_crl'),
    url(r'^no-auth/glpi/rpc$', 'penatesserver.glpi.views.xmlrpc'),
    url(r'^auth/get_user_certificate/$', 'penatesserver.pki.views.get_user_certificate'),
    url(r'^auth/get_email_certificate/$', 'penatesserver.pki.views.get_email_certificate'),
    url(r'^auth/get_signature_certificate/$', 'penatesserver.pki.views.get_signature_certificate'),
    url(r'^auth/get_encipherment_certificate/$', 'penatesserver.pki.views.get_encipherment_certificate'),
    url(r'^auth/get_mobileconfig/profile.mobileconfig$', 'penatesserver.views.get_user_mobileconfig'),
    url(r'^auth/api/', include('rest_framework.urls', namespace='rest_framework')),
]
