# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.http import HttpResponse

from penatesserver.models import Host, Service

__author__ = 'Matthieu Gallet'

check_commands = {}


def get_shinken_config(request):
    r = {'commands': [], 'timeperiods': [], 'hosts': [], 'hostgroups': [],
         'servicestemplates': [], 'services': [], 'contacts': []}
    for host_obj in Host.objects.all():
        host = {'host_name': host_obj.fqdn,
                'display_name': host_obj.fqdn.partition('.')[0],
                'address': host_obj.main_ip_address,
                # 'parents': None,  # host_names
                # 'hostgroups': None,  # hostgroup_names
                'realm': host_obj.fqdn.partition('.')[2],
                'contacts': 'admin', }
        r['hosts'].append(host)
    for service_obj in Service.objects.all():
        if service_obj.scheme not in check_commands:
            continue
        for command in check_commands.get(service_obj.scheme, []):
            command = command % {'fqdn': service_obj.fqdn,
                                 'scheme': service_obj.scheme,
                                 'hostname': service_obj.hostname,
                                 'port': service_obj.port,
                                 'protocol': service_obj.protocol,
                                 'encryption': service_obj.encryption,
                                 'ssl_suffix': 's' if service_obj.encryption == 'ssl' else '',
                                 'kerberos_service': service_obj.kerberos_service, }
            service = {'host_name': service_obj.fqdn,
                       'service_description': service_obj.description,
                       'display_name': service_obj.hostname,
                       'servicegroups': service_obj.scheme,
                       'check_interval': '5',
                       'retry_interval': '3',
                       'check_period': '24x7',
                       'check_command': command,
                       'notification_interval': '30',
                       'notification_period': '24x7',
                       'notification_options': 'w,c,r',
                       'contacts': 'admin', }
            r['services'].append(service)
    content = json.dumps(r, encoding='utf-8', ensure_ascii=False)
    return HttpResponse(content, content_type='text/json')
