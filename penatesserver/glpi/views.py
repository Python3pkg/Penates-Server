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

shinken_checks = {
    # 'penates_dhcp': 'check_dhcp -r $ARG2$ -m $ARG1$',
    'penates_dig': 'check_dig -l $ARG1$ -a $HOSTADDRESS$',
    'penates_dig_2': 'check_dig -l $ARG1$ -a $ARG2$',
    'penates_http': 'check_http -H $ARG1$ -p $ARG2$',
    'penates_https': 'check_http -S --sni -H $ARG1$ -p $ARG2$ -C 15 -e 401',
    'penates_imap': 'check_imap -H $HOSTNAME$ -p $ARG1$',
    'penates_imaps': 'check_imap -H $HOSTNAME$ -p $ARG1$ -S -D 15',
    'penates_ldap': 'check_ldap -H $HOSTADDRESS$ -p $ARG1$ -3',
    'penates_ldaps': 'check_ldaps -H $HOSTADDRESS$ -p $ARG1$ -3',
    'penates_ntp': 'check_ntp_peer -H $HOSTADDRESS$',
    'penates_smtp': 'check_smtp -H $HOSTADDRESS$ -p $ARG1$',
    'penates_smtps': 'check_smtp -H $HOSTADDRESS$ -p $ARG1$ -S -D 15',
    'penates_udp': 'check_udp -H $HOSTADDRESS$ -p $ARG1$'
}


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
    end_time = int((datetime.datetime.utcnow() - year_0).total_seconds()) + session_duration_in_seconds
    session = '%s:%s' % (end_time, login_name)
    session = signer.sign(session)
    return {'session': session, }


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenCommands')
def shinken_commands(request, args):
    check_session(request, args)
    return [{'command_name': key, 'command_line': '$PLUGINSDIR$/%s' % value} for (key, value) in shinken_checks.items()]


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
        result.append({'use': 'local-service', 'host_name': host.fqdn,
                       'service_description': _('Check SSH %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_ssh',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service', 'host_name': host.fqdn,
                       'service_description': _('Ping %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_ping!100.0,20%!500.0,60%',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check all disks on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_all_disk',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check swap on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_swap',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check number of processes on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_total_procs',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check number of zombie processes on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_zombie_procs',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check load on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_load',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service', 'host_name': host.fqdn,
                       'service_description': _('Check DNS %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'penates_dig_2!%s!%s' % (host.fqdn, host.main_ip_address),
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service', 'host_name': host.fqdn,
                       'service_description': _('Check DNS %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'penates_dig_2!%s!%s' % (host.admin_fqdn, host.admin_ip_address),
                       'notifications_enabled': '0', })

    for service in Service.objects.all():
        if service.scheme == 'http':
            check = 'penates_http!%s!%s' if service.encryption == 'none' else 'penates_https!%s!%s'
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('HTTP on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': check % (service.hostname, service.port),
                           'notifications_enabled': '0', })
        elif service.scheme == 'ssh':
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('SSH TCP on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': 'check_tcp!%s' % service.port,
                           'notifications_enabled': '0', })
            result.append({'use': 'generic-service', 'host_name': service.fqdn,
                           'service_description': _('SSH process on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': 'check_nrpe!check_sshd', 'notifications_enabled': '0', })
        elif service.scheme == 'imap':
            check = 'penates_imaps!%s' if service.encryption == 'tls' else 'penates_imap!%s'
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('IMAP on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': check % service.port,
                           'notifications_enabled': '0', })
        elif service.scheme == 'ldap':
            check = 'penates_ldaps!%s' if service.encryption == 'tls' else 'penates_ldap!%s'
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('LDAP on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': check % service.port,
                           'notifications_enabled': '0', })
        elif service.scheme == 'smtp':
            check = 'penates_smtps!%s' if service.encryption == 'tls' else 'penates_smtp!%s'
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('SMTP on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': check % service.port,
                           'notifications_enabled': '0', })
        elif service.scheme == 'ntp':
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('NTP on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': 'penates_ntp!%s' % service.hostname,
                           'notifications_enabled': '0', })
        elif service.scheme == 'dkim':
            pass
        elif service.protocol == 'tcp':
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('TCP on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': 'check_tcp!%s' % service.port,
                           'notifications_enabled': '0', })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenContacts')
def shinken_contacts(request, args):
    check_session(request, args)
    result = []
    for user in User.objects.all():
        result.append({'contact_name': user.name, 'alias': user.display_name, 'use': 'generic-contact',
                       'password': 'toto', 'email': user.mail, 'is_admin': '1' if user.name.endswith('_admin') else '0',
                       })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenTimeperiods')
def shinken_time_periods(request, args):
    check_session(request, args)
    return []
