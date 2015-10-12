# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.core.signing import Signer
from penatesserver.glpi.xmlrpc import XMLRPCSite
from penatesserver.glpi.xmlrpc import register_rpc_method
from penatesserver.models import Host, Service, User, AdminUser
from django.utils.translation import ugettext as _

__author__ = 'Matthieu Gallet'

XML_RPC_SITE = XMLRPCSite()
signer = Signer()
year_0 = datetime.datetime(1970, 1, 1, 0, 0, 0)
session_duration_in_seconds = 600


def xmlrpc(request):
    return XML_RPC_SITE.dispatch(request)


def check_session(request, args):
    session = args[0]['session']
    session = signer.unsign(session)
    end, sep, login_name = session.partition(':')
    end = int(end)
    if (datetime.datetime.utcnow() - year_0).total_seconds() > end:
        raise ValueError


@register_rpc_method(XML_RPC_SITE, name='glpi.doLogin')
def do_login(request, args):
    login_name = args[0]['login_name'].decode('utf-8')
    login_password = args[0]['login_password'].decode('utf-8')
    users = list(AdminUser.objects.filter(username=login_name, user_permissions__codename='supervision')[0:1])
    if not users:
        raise PermissionDenied
    user = users[0]
    if not user.check_password(login_password):
        raise PermissionDenied
    Permission.objects.filter()
    end_time = (datetime.datetime.utcnow() - year_0).total_seconds() + session_duration_in_seconds
    session = '%s:%s' % (end_time, login_name)
    session = signer.sign(session)
    return {'session': session, }


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenCommands')
def shinken_commands(request, args):
    check_session(request, args)
    return []


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenHosts')
def shinken_hosts(request, args):
    check_session(request, args)
    result = []
    for host in Host.objects.all():
        # noinspection PyTypeChecker
        result.append({
            'host_name': host.fqdn,
            'alias': '%s,%s' % (host.admin_fqdn, host.fqdn.partition('.')[0]),
            'display_name': host.fqdn,
            'address': host.admin_ip_address,
        })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenHostgroups')
def shinken_host_groups(request, args):
    check_session(request, args)
    return []


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenTemplates')
def shinken_templates(request, args):
    check_session(request, args)
    return []


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenServices')
def shinken_services(request, args):
    check_session(request, args)
    result = []
    for host in Host.objects.all():
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check SSH %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_ssh',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Ping %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_ping!100.0,20%!500.0,60%',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check / on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_disk!20%!10%!/',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check logged local users on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_users!10!30',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check currently running procs on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_procs!250!400!RSZDT',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Check current load on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_load!5.0,4.0,3.0!10.0,6.0,4.0',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service',
                       'host_name': host.fqdn,
                       'service_description': _('Swap usage on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_local_swap!20!10',
                       'notifications_enabled': '0', })
    for service in Service.objects.all():
        if service.scheme == 'http' and not service.encryption == 'none':
            result.append({'use': 'local-service',
                           'host_name': service.hostname,
                           'service_description': _('Check HTTP on %(fqdn)s') % {'fqdn': service.hostname, },
                           'check_command': 'check_http',
                           'notifications_enabled': '0', })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenContacts')
def shinken_contacts(request, args):
    check_session(request, args)
    result = []
    for user in User.objects.all():
        result.append({'contact_name': user.name, 'alias': user.display_name, 'use': 'generic-contact', 'password': 'toto',
                       'email': user.mail, 'is_admin': '1' if user.name.endswith('_admin') else '0',
        })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenTimeperiods')
def shinken_time_periods(request, args):
    check_session(request, args)
    return []
