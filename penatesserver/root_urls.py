# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url

from rest_framework import routers
from penatesserver.glpi.views import xmlrpc, register_service

from penatesserver.models import name_pattern
from penatesserver.pki.views import get_host_certificate, get_ca_certificate, get_admin_certificate, \
    get_service_certificate, get_crl, get_user_certificate, get_email_certificate, get_signature_certificate, \
    get_encipherment_certificate
from penatesserver.views import GroupDetail, GroupList, UserDetail, UserList, get_host_keytab, get_info, set_dhcp, \
    get_dhcpd_conf, get_dns_conf, set_mount_point, set_ssh_pub, set_service, set_extra_service, get_service_keytab, \
    change_own_password, get_user_mobileconfig, index

__author__ = 'flanker'

router = routers.DefaultRouter()

service_pattern = r'(?P<scheme>\w+)/(?P<hostname>[a-zA-Z0-9\.\-_]+)/(?P<port>\d+)/'
app_name = 'penatesserver'
urls = [
    url('^index$', index, name='index'),
    url(r'^', include(router.urls)),
    url(r'^no-auth/get_host_keytab/(?P<hostname>[a-zA-Z0-9\.\-_]+)$', get_host_keytab, name='get_host_keytab'),
    url(r'^auth/get_info/$', get_info, name='get_info'),
    url(r'^auth/set_dhcp/(?P<mac_address>([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})/$', set_dhcp, name='set_dhcp'),
    url(r'^auth/conf/dhcpd.conf$', get_dhcpd_conf, name='get_dhcpd_conf'),
    url(r'^auth/conf/dns.conf$', get_dns_conf, name='get_dns_conf'),
    url(r'^auth/set_mount_point/$', set_mount_point, name='set_mount_point'),
    url(r'^auth/set_ssh_pub/$', set_ssh_pub, name='set_ssh_pub'),
    url(r'^auth/set_service/%s$' % service_pattern, set_service, name='set_service'),
    url(r'^auth/set_extra_service/(?P<hostname>[a-zA-Z0-9\.\-_]+)$', set_extra_service, name='set_extra_service'),
    url(r'^auth/get_service_keytab/%s$' % service_pattern, get_service_keytab, name='get_service_keytab'),
    url(r'^auth/user/$', UserList.as_view(), name='user_list'),
    url(r'^auth/user/(?P<name>%s)$' % name_pattern, UserDetail.as_view(), name='user_detail'),
    url(r'^auth/group/$', GroupList.as_view(), name='group_list'),
    url(r'^auth/group/(?P<name>%s)$' % name_pattern, GroupDetail.as_view(), name='group_detail'),
    url(r'^auth/change_password/$', change_own_password, name='change_own_password'),
    url(r'^auth/get_host_certificate/$', get_host_certificate, name='get_host_certificate'),
    url(r'^auth/get_admin_certificate/$', get_admin_certificate, name='get_admin_certificate'),
    url(r'^auth/get_service_certificate/%s$' % service_pattern, get_service_certificate,
        name='get_service_certificate'),
    url(r'^auth/glpi/register_service/(?P<check_command>.*)$', register_service, name='register_service'),
    url(r'^no-auth/(?P<kind>ca|users|hosts|services).pem$', get_ca_certificate, name='get_ca_certificate'),
    url(r'^no-auth/crl.pem$', get_crl, name='get_crl'),
    url(r'^no-auth/glpi/rpc$', xmlrpc, name='xmlrpc'),
    url(r'^auth/get_user_certificate/$', get_user_certificate, name='get_user_certificate'),
    url(r'^auth/get_email_certificate/$', get_email_certificate, name='get_email_certificate'),
    url(r'^auth/get_signature_certificate/$', get_signature_certificate, name='get_signature_certificate'),
    url(r'^auth/get_encipherment_certificate/$', get_encipherment_certificate, name='get_encipherment_certificate'),
    url(r'^auth/get_mobileconfig/profile.mobileconfig$', get_user_mobileconfig, name='get_user_mobileconfig'),
    url(r'^auth/api/', include('rest_framework.urls', namespace='rest_framework')),
]
