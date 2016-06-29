# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.core.signing import Signer
from django.utils.six import text_type
from django.utils.translation import ugettext as _
from penatesserver.glpi.models import ShinkenService
from penatesserver.models import Host, Service

__author__ = 'Matthieu Gallet'
signer = Signer()
year_0 = datetime.datetime(1970, 1, 1, 0, 0, 0)
session_duration_in_seconds = 600


# noinspection PyUnusedLocal
def check_session(request, args):
    session = args[0]['session']
    session = signer.unsign(session)
    end, sep, login_name = session.partition(':')
    end = int(end)
    if (datetime.datetime.utcnow() - year_0).total_seconds() > end:
        raise ValueError


def get_shinken_services():
    result = []
    for host in Host.objects.all():
        result.append({'use': 'local-service', 'host_name': host.fqdn,
                       'service_description': _('Check SSH %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_ssh',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service', 'host_name': host.fqdn,
                       'service_description': _('Ping %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_ping!100.0,20%!500.0,60%', 'icon_set': 'server',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check all disks on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_all_disk', 'icon_set': 'disk',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check swap on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_swap',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check number of processes on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_total_procs', 'icon_set': 'server',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check number of zombie processes on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_zombie_procs', 'icon_set': 'server',
                       'notifications_enabled': '0', })
        result.append({'use': 'generic-service', 'host_name': host.fqdn,
                       'service_description': _('Check load on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_load', 'icon_set': 'server',
                       'notifications_enabled': '0', })
        result.append({'use': 'local-service', 'host_name': host.fqdn, 'icon_set': 'server',
                       'service_description': _('Check DNS %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'penates_dig_2!%s!%s' % (host.fqdn, host.main_ip_address),
                       'notifications_enabled': '0', 'check_interval': text_type(4 * 60), })
        result.append({'use': 'local-service', 'host_name': host.fqdn, 'icon_set': 'server',
                       'service_description': _('Check DNS %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'penates_dig_2!%s!%s' % (host.admin_fqdn, host.admin_ip_address),
                       'notifications_enabled': '0', 'check_interval': text_type(4 * 60), })
        result.append({'use': 'generic-service', 'host_name': host.fqdn, 'icon_set': 'server',
                       'service_description': _('Check admin certificate on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_cert_admin',
                       'notifications_enabled': '0', 'check_interval': text_type(24 * 60), })
        result.append({'use': 'generic-service', 'host_name': host.fqdn, 'icon_set': 'server',
                       'service_description': _('Check host certificate on %(fqdn)s') % {'fqdn': host.fqdn, },
                       'check_command': 'check_nrpe!check_cert_host',
                       'notifications_enabled': '0', 'check_interval': text_type(24 * 60), })
    for service in Service.objects.all():
        if service.scheme in ('http', 'carddav', 'caldav'):
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
            check = 'penates_ldaps!%s!%s' if service.encryption == 'tls' else 'penates_ldap!%s!%s'
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('LDAP on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': check % (service.hostname, service.port),
                           'notifications_enabled': '0', })
        elif service.scheme == 'krb':
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('Kerberos on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': 'check_tcp!%s' % service.port,
                           'notifications_enabled': '0', })
        elif service.scheme == 'dns':
            result.append({'use': 'local-service',
                           'host_name': service.fqdn,
                           'service_description': _('DNS on %(fqdn)s:%(port)s') %
                           {'fqdn': service.hostname, 'port': service.port, },
                           'check_command': 'penates_dns',
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
    for service in ShinkenService.objects.all():
        result.append(service.to_dict())
    return result
