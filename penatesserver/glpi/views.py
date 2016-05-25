# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt

from penatesserver.glpi.forms import ShinkenServiceForm
from penatesserver.glpi.models import ShinkenService
from penatesserver.glpi.services import get_shinken_services, year_0, session_duration_in_seconds, signer, check_session
from penatesserver.glpi.xmlrpc import XMLRPCSite
from penatesserver.glpi.xmlrpc import register_rpc_method
from penatesserver.models import Host, User, AdminUser
from penatesserver.utils import hostname_from_principal, is_admin


__author__ = 'Matthieu Gallet'

XML_RPC_SITE = XMLRPCSite()

shinken_checks = {
    # 'penates_dhcp': 'check_dhcp -r $ARG2$ -m $ARG1$',
    'penates_dig': 'check_dig -l $ARG1$ -a $HOSTADDRESS$ -H %s' % settings.SERVER_NAME,
    'penates_dig_2': 'check_dig -l $ARG1$ -a $ARG2$ -H %s' % settings.SERVER_NAME,
    'penates_http': 'check_http -H $ARG1$ -p $ARG2$',
    'penates_https': 'check_http -S --sni -H $ARG1$ -p $ARG2$ -C 15 -e 401',
    'penates_imap': 'check_imap -H $HOSTNAME$ -p $ARG1$',
    'penates_imaps': 'check_simap -H $HOSTNAME$ -p $ARG1$ -D 15',
    'penates_ldap': 'check_ldap -H $ARG1$ -b %s -p $ARG2$ -3' % settings.LDAP_BASE_DN,
    'penates_ldaps': 'check_ldaps -H $ARG1$ -b %s -p $ARG2$ -3' % settings.LDAP_BASE_DN,
    'penates_ntp': 'check_ntp_peer -H $HOSTADDRESS$',
    'penates_smtp': 'check_smtp -H $HOSTADDRESS$ -p $ARG1$',
    'penates_smtps': 'check_ssmtp -H $HOSTADDRESS$ -p $ARG1$ -D 15',
    'penates_udp': 'check_udp -H $HOSTADDRESS$ -p $ARG1$',
    'penates_dns': 'check_dns -H $HOSTADDRESS$',
}


@csrf_exempt
def xmlrpc(request):
    return XML_RPC_SITE.dispatch(request)


@login_required
def register_service(request, check_command):
    fqdn = hostname_from_principal(request.user.username)
    status = 204
    if request.method == 'POST':
        if request.body:
            content = json.loads(request.body.decode('utf-8'))
            s = ShinkenService(**content)
            s.host_name = fqdn
            values = s.to_dict()
        for key in ('host_name', 'check_command'):
            if key in values:
                del values[key]
        if ShinkenService.objects.filter(host_name=fqdn, check_command=check_command)\
                .update(**values) == 0:
            ShinkenService(host_name=fqdn, check_command=check_command, **values).save()
            return HttpResponse(status=201)
    elif request.method == 'GET':
        form = ShinkenServiceForm(request.GET)
        if not form.is_valid():
            return HttpResponse(status=400)
        values = {key: value for key, value in form.cleaned_data.items() if value}
        if ShinkenService.objects.filter(host_name=fqdn, check_command=check_command)\
                .update(**values) == 0:
            ShinkenService(host_name=fqdn, check_command=check_command, **values).save()
            return HttpResponse(status=201)
    elif request.method == 'DELETE':
        ShinkenService.objects.filter(host_name=fqdn, check_command=check_command).delete()
        status = 202
    return HttpResponse(status=status)


# noinspection PyUnusedLocal
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
    return get_shinken_services()


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenContacts')
def shinken_contacts(request, args):
    check_session(request, args)
    result = []
    for user in User.objects.all():
        result.append({'contact_name': user.name, 'alias': user.display_name, 'use': 'generic-contact',
                       'password': get_random_string(), 'email': user.mail,
                       'is_admin': '1' if is_admin(user.name) else '0', })
    return result


@register_rpc_method(XML_RPC_SITE, name='monitoring.shinkenTimeperiods')
def shinken_time_periods(request, args):
    check_session(request, args)
    return []
