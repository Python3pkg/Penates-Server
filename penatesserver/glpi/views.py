# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.core.signing import Signer
from penatesserver.glpi.xmlrpc import XMLRPCSite
from penatesserver.glpi.xmlrpc import register_rpc_method
from penatesserver.models import Host, Service, User
from django.utils.translation import ugettext as _

__author__ = 'Matthieu Gallet'

XML_RPC_SITE = XMLRPCSite()
signer = Signer()
year_0 = datetime.datetime(1970, 1, 1, 0, 0, 0)
session_duration = 3600


def xmlrpc(request):
    return XML_RPC_SITE.dispatch(request)


def check_session(session):
    return True
    session = signer.unsign(session)
    end, sep, login_name = session.partition(':')
    end = int(end)
    if (datetime.datetime.utcnow() - year_0).total_seconds() > end:
        raise ValueError


@register_rpc_method(XML_RPC_SITE, name='glpi.doLogin')
def do_login(request, login_name=None, login_password=None):
    session = '%s:%s' % ((datetime.datetime.utcnow() - year_0).total_seconds() + session_duration, login_name)
    session = signer.sign(session)
    return {'session': session, }


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenCommands')
def shinken_commands(request, session=None, iso8859=None, tag=None):
    check_session(session)
    return []


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenHosts')
def shinken_hosts(request, session=None, iso8859=None, tag=None):
    check_session(session)
    result = []
    for host in Host.objects.all():
        # noinspection PyTypeChecker
        result.append({
            'hostname': host.fqdn,
            'alias': '%s,%s' % (host.admin_fqdn, host.fqdn.partition('.')[0]),
            'display_name': host.fqdn,
            'address': host.admin_ip_address,
        })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenHostgroups')
def shinken_host_groups(request, session=None, iso8859=None, tag=None):
    check_session(session)
    return [{'hostgroup_name': 'Servers', 'realm': 'penates', }, ]


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenTemplates')
def shinken_templates(request, session=None, iso8859=None, tag=None):
    check_session(session)
    return []


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenServices')
def shinken_services(request, session=None, iso8859=None, tag=None):
    check_session(session)
    result = []
    for host in Host.objects.all():
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check SSH %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_ssh',
                       'notifications_enabled': 0, })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Ping %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_ping!100.0,20%!500.0,60%',
                       'notifications_enabled': 0, })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check / on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_disk!20%!10%!/',
                       'notifications_enabled': 0, })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check logged local users on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_users!10!30',
                       'notifications_enabled': 0, })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check currently running procs on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_procs!250!400!RSZDT',
                       'notifications_enabled': 0, })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check current load on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_load!5.0,4.0,3.0!10.0,6.0,4.0',
                       'notifications_enabled': 0, })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Swap usage on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_swap!20!10',
                       'notifications_enabled': 0, })
    for service in Service.objects.all():
        if service.scheme == 'http' and not service.encryption == 'none':
            result.append({'use': 'local-service',
                           'host_name': service.hostname,
                           'service_description': _('Check HTTP on %(fqdn)s') % {'fqdn': service.hostname, },
                           'check_command': 'check_http',
                           'notifications_enabled': 0, })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenContacts')
def shinken_contacts(request, session=None, iso8859=None, tag=None):
    check_session(session)
    result = []
    for user in User.objects.all():
        result.append({'contact_name': user.name, 'alias': user.display_name, 'use': 'generic-contact', 'password': 'toto',
                       'email': user.mail, 'is_admin': '1' if user.name.endswith('_admin') else '0',
        })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenTimeperiods')
def shinken_time_periods(request, session=None, iso8859=None, tag=None):
    return []
