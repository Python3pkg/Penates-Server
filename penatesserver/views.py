# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import base64
import hashlib
import os
import re
import tempfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
import netaddr
from django.views.decorators.csrf import csrf_protect
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from penatesserver.forms import PasswordForm
from penatesserver.kerb import add_principal_to_keytab, add_principal, principal_exists
from penatesserver.models import Service, Host, User, Group, MountPoint
from penatesserver.pki.constants import COMPUTER, SERVICE, KERBEROS_DC, PRINTER, TIME_SERVER, SERVICE_1024
from penatesserver.pki.service import CertificateEntry, PKI
from penatesserver.powerdns.models import Domain, Record
from penatesserver.serializers import UserSerializer, GroupSerializer
from penatesserver.subnets import get_subnets
from penatesserver.utils import hostname_from_principal, principal_from_hostname

__author__ = 'flanker'


class KeytabResponse(HttpResponse):
    def __init__(self, principal, **kwargs):
        with tempfile.NamedTemporaryFile() as fd:
            keytab_filename = fd.name
        add_principal_to_keytab(principal, keytab_filename)
        # noinspection PyTypeChecker
        with open(keytab_filename, 'rb') as fd:
            keytab_content = bytes(fd.read())
        os.remove(keytab_filename)
        super(KeytabResponse, self).__init__(content=keytab_content, content_type='application/keytab', **kwargs)


def entry_from_hostname(hostname):
    return CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION,
                            organizationalUnitName=_('Computers'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                            localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                            stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=COMPUTER)


def admin_entry_from_hostname(hostname):
    return CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION,
                            organizationalUnitName=_('Computers'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                            localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                            stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=COMPUTER)


@login_required
def index(request):
    template_values = {'protocol': settings.PROTOCOL,
                       'server_name': settings.SERVER_NAME,
                       }
    return render_to_response('penatesserver/index.html', template_values, RequestContext(request))


@login_required
def get_info(request):
    content = ''
    content += 'METHOD:%s\n' % request.method
    content += 'REMOTE_USER:%s\n' % ('' if request.user.is_anonymous() else request.user.username)
    content += 'REMOTE_ADDR:%s\n' % request.META.get('HTTP_X_FORWARDED_FOR', '')
    content += 'HTTPS?:%s\n' % request.is_secure()
    return HttpResponse(content, status=200, content_type='text/plain')


def get_host_keytab(request, hostname):
    """Register a computer:

        - create Kerberos principal
        - create private key
        - create public SSH key
        - create x509 certificate
        - create PTR DNS record
        - create A or AAAA DNS record
        - create SSHFP DNS record
        - return keytab

    :param request:
    :type request:
    :param hostname:
    :type hostname:
    :return:
    :rtype:
    """
    admin_ip_address = request.GET.get('ip_address')
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    short_hostname = hostname.partition('.')[0]
    domain_name = settings.PENATES_DOMAIN
    fqdn = '%s.%s%s' % (short_hostname, settings.PDNS_INFRA_PREFIX, domain_name)
    # valid FQDN
    # create Kerberos principal
    principal = principal_from_hostname(fqdn, settings.PENATES_REALM)
    if principal_exists(principal):
        return HttpResponse('', status=403)
    else:
        add_principal(principal)
    Host.objects.get_or_create(fqdn=fqdn)
    # create private key, public key, public certificate, public SSH key
    entry = entry_from_hostname(fqdn)
    pki = PKI()
    pki.ensure_certificate(entry)
    # create DNS records
    if ip_address:
        Domain.ensure_auto_record(ip_address, fqdn, unique=True, override_reverse=True)
        Host.objects.filter(fqdn=fqdn).update(main_ip_address=ip_address)
    if admin_ip_address:
        admin_fqdn = '%s.%s%s' % (short_hostname, settings.PDNS_ADMIN_PREFIX, domain_name)
        Domain.ensure_auto_record(admin_ip_address, admin_fqdn, unique=True, override_reverse=False)
        Host.objects.filter(fqdn=fqdn).update(admin_ip_address=admin_ip_address)
    if settings.OFFER_HOST_KEYTABS:
        return KeytabResponse(principal)
    return HttpResponse('', content_type='text/plain', status=201)


@login_required
def set_dhcp(request, mac_address):
    hostname = hostname_from_principal(request.user.username)
    mac_address = mac_address.replace('-', ':').upper()
    remote_addr = request.META.get('HTTP_X_FORWARDED_FOR', '')
    admin_mac_address = request.GET.get('mac_address')
    admin_ip_address = request.GET.get('ip_address')
    admin_mac_address = admin_mac_address.replace('-', ':').upper()
    if remote_addr:
        Host.objects.filter(fqdn=hostname).update(main_ip_address=remote_addr, main_mac_address=mac_address)
        Record.objects.filter(name=hostname).update(content=remote_addr)
    if admin_ip_address and admin_mac_address:
        domain_name = '%s%s' % (settings.PDNS_ADMIN_PREFIX, settings.PENATES_DOMAIN)
        long_admin_hostname = '%s.%s' % (hostname.partition('.')[0], domain_name)
        Host.objects.filter(fqdn=hostname)\
            .update(admin_ip_address=admin_ip_address, admin_mac_address=admin_mac_address)
        Domain.ensure_auto_record(admin_ip_address, long_admin_hostname, unique=True, override_reverse=False)
    return HttpResponse(status=201)


@login_required
def set_mount_point(request):
    hostname = hostname_from_principal(request.user.username)
    hosts = list(Host.objects.filter(fqdn=hostname)[0:1])
    if not hosts:
        return HttpResponse(status=404)
    host = hosts[0]
    mount_point = request.GET.get('mount_point')
    if not mount_point:
        return HttpResponse('mount_point GET argument not provided', status=400)
    device = request.GET.get('device')
    if not device:
        return HttpResponse('device GET argument not provided', status=400)
    fs_type = request.GET.get('fs_type')
    if not fs_type:
        return HttpResponse('fs_type GET argument not provided', status=400)
    options = request.GET.get('options')
    if not options:
        return HttpResponse('options GET argument not provided', status=400)
    if MountPoint.objects.filter(host=host, mount_point=mount_point)\
            .update(fs_type=fs_type, device=device, options=options) == 1:
        return HttpResponse('', status=204)
    MountPoint(host=host, mount_point=mount_point, fs_type=fs_type, device=device, options=options).save()
    return HttpResponse('', status=201)


@login_required
def set_ssh_pub(request):
    fqdn = hostname_from_principal(request.user.username)
    if Host.objects.filter(fqdn=fqdn).count() == 0:
        return HttpResponse(status=404)
    fqdn = '%s.%s%s' % (fqdn.partition('.')[0], settings.PDNS_ADMIN_PREFIX, settings.PENATES_DOMAIN)
    domain_name = '%s%s' % (settings.PDNS_ADMIN_PREFIX, settings.PENATES_DOMAIN)
    pub_ssh_key = request.body
    matcher = re.match(r'([\w\-]+) ([\w\+=/]{1,5000})(|\s.*)$', pub_ssh_key)
    if not matcher:
        return HttpResponse(status=406, content='Invalid public SSH key')
    methods = {'ssh-rsa': 1, 'ssh-dss': 2, 'ecdsa-sha2-nistp256': 3, 'ssh-ed25519': 4, }
    if matcher.group(1) not in methods:
        return HttpResponse(status=406, content='Unknown SSH key type %s' % matcher.group(1))
    sha1_hash = hashlib.sha1(base64.b64decode(matcher.group(2))).hexdigest()
    sha256_hash = hashlib.sha256(base64.b64decode(matcher.group(2))).hexdigest()
    algorithm_code = methods[matcher.group(1)]
    domain = Domain.objects.get(name=domain_name)
    sha1_value = '%s 1 %s' % (algorithm_code, sha1_hash)
    sha256_value = '%s 2 %s' % (algorithm_code, sha256_hash)
    for value in sha1_value, sha256_value:
        if Record.objects.filter(domain=domain, name=fqdn, type='SSHFP', content__startswith=value[:4]).count() == 0:
            Record(domain=domain, name=fqdn, type='SSHFP', content=value, ttl=86400).save()
        else:
            Record.objects.filter(domain=domain, name=fqdn, type='SSHFP', content__startswith=value[:4])\
                .update(content=value)
    return HttpResponse(status=201)


@login_required
def set_extra_service(request, hostname):
    ip_address = request.GET.get('ip', '')
    try:
        addr = netaddr.IPAddress(ip_address)
    except ValueError:
        return HttpResponse(status=403, content='Invalid IP address ?ip=%s' % ip_address)
    record_type = 'A' if addr.version == 4 else 'AAAA'
    sqdn, sep, domain_name = hostname.partition('.')
    if domain_name != settings.PENATES_DOMAIN:
        return HttpResponse(status=403, content='Unknown domain %s' % domain_name)
    domain = Domain.objects.get(name=domain_name)
    Record.objects.get_or_create(domain=domain, name=hostname, type=record_type, content=ip_address)
    return HttpResponse(status=201)


@login_required
def set_service(request, scheme, hostname, port):
    encryption = request.GET.get('encryption', 'none')
    srv_field = request.GET.get('srv', None)
    kerberos_service = request.GET.get('keytab', None)
    role = request.GET.get('role', SERVICE)
    protocol = request.GET.get('protocol', 'tcp')

    if encryption not in ('none', 'tls', 'starttls'):
        return HttpResponse('valid encryption levels are none, tls, or starttls')
    port = int(port)
    if not (0 <= port <= 65536):
        return HttpResponse('Invalid port: %s' % port, status=403, content_type='text/plain')
    if protocol not in ('tcp', 'udp', 'socket'):
        return HttpResponse('Invalid protocol: %s' % protocol, status=403, content_type='text/plain')
    description = request.body
    fqdn = hostname_from_principal(request.user.username)
    # a few checks
    if Service.objects.filter(hostname=hostname).exclude(fqdn=fqdn).count() > 0:
        return HttpResponse(status=401, content='%s is already registered' % hostname)
    if role not in (SERVICE, KERBEROS_DC, PRINTER, TIME_SERVER, SERVICE_1024):
        return HttpResponse(status=401, content='Role %s is not allowed' % role)
    if kerberos_service and kerberos_service not in settings.KERBEROS_SERVICES:
        return HttpResponse(status=401, content='Kerberos service %s is not allowed' % role)
    hosts = list(Host.objects.filter(fqdn=fqdn)[0:1])
    if not hosts:
        return HttpResponse(status=401, content='Unknown host %s is not allowed' % fqdn)
    host = hosts[0]
    if scheme == 'ssh' and host.admin_ip_address != host.main_ip_address:
        fqdn = '%s.%s%s' % (fqdn.partition('.')[0], settings.PDNS_ADMIN_PREFIX, settings.PENATES_DOMAIN)

    # Penates service
    service, created = Service.objects.get_or_create(fqdn=fqdn, scheme=scheme, hostname=hostname, port=port,
                                                     protocol=protocol,
                                                     defaults={'kerberos_service': kerberos_service,
                                                               'dns_srv': srv_field, 'encryption': encryption,
                                                               'description': description})
    Service.objects.filter(pk=service.pk).update(kerberos_service=kerberos_service, description=description,
                                                 dns_srv=srv_field, encryption=encryption)
    # certificates
    entry = CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION,
                             organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                             localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                             stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=role)
    pki = PKI()
    pki.ensure_certificate(entry)
    if kerberos_service:
        add_principal(service.principal_name)
    # DNS part
    record_name, sep, domain_name = hostname.partition('.')
    if sep == '.':
        domains = list(Domain.objects.filter(name=domain_name)[0:1])
        if domains:
            domain = domains[0]
            domain.ensure_record(fqdn, hostname)
            domain.set_extra_records(scheme, hostname, port, fqdn, srv_field, entry=entry)
            domain.update_soa()
    return HttpResponse(status=201, content='%s://%s:%s/ created' % (scheme, hostname, port))


@login_required
def get_service_keytab(request, scheme, hostname, port):
    fqdn = hostname_from_principal(request.user.username)
    protocol = request.GET.get('protocol', 'tcp')
    hosts = list(Host.objects.filter(fqdn=fqdn)[0:1])
    if not hosts:
        return HttpResponse(status=401, content='Unknown host %s is not allowed' % fqdn)
    host = hosts[0]
    if scheme == 'ssh' and host.admin_ip_address != host.main_ip_address:
        fqdn = '%s.%s%s' % (fqdn.partition('.')[0], settings.PDNS_ADMIN_PREFIX, settings.PENATES_DOMAIN)
    services = list(Service.objects.filter(fqdn=fqdn, scheme=scheme, hostname=hostname, port=port,
                                           protocol=protocol)[0:1])
    if not services:
        return HttpResponse(status=404, content='%s://%s:%s/ unknown' % (scheme, hostname, port))
    service = services[0]
    if not principal_exists(service.principal_name):
        return HttpResponse(status=404, content='Principal for %s://%s:%s/ undefined' % (scheme, hostname, port))
    return KeytabResponse(service.principal_name)


def get_dhcpd_conf(request):
    def get_ip_or_none(scheme):
        values = list(Service.objects.filter(scheme=scheme)[0:1])
        if not values:
            return None
        return Record.local_resolve(values[0].fqdn) or values[0].hostname

    def get_ip_list(scheme):
        values = list(Service.objects.filter(scheme=scheme))
        return [Record.local_resolve(x.fqdn) or x.hostname for x in values]

    template_values = {
        'penates_subnets': get_subnets(),
        'penates_domain': settings.PENATES_DOMAIN,
        'admin_prefix': settings.PDNS_ADMIN_PREFIX,
        'infra_prefix': settings.PDNS_INFRA_PREFIX,
        'hosts': Host.objects.all(),
        'tftp': get_ip_or_none('tftp'),
        'dns_list': get_ip_list('dns'),
        'ntp': get_ip_or_none('ntp'),
    }
    return render_to_response('dhcpd/dhcpd.conf', template_values, status=200, content_type='text/plain')


def get_dns_conf(request):
    domains = {}
    for domain in Domain.objects.all():
        domains[domain.id] = (domain, [])
    for record in Record.objects.all():
        domains[record.domain_id][1].append(record)
    template_values = {'domains': domains, }
    return render_to_response('dns/dns.conf', template_values, status=200, content_type='text/plain')


@method_decorator(csrf_protect, name='post')
class UserList(ListCreateAPIView):
    """
    List all users, or create a new user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'name'


@method_decorator(csrf_protect, name='put')
@method_decorator(csrf_protect, name='patch')
@method_decorator(csrf_protect, name='delete')
class UserDetail(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a user instance.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'name'


@method_decorator(csrf_protect, name='post')
class GroupList(ListCreateAPIView):
    """
    List all groups, or create a new group.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    lookup_field = 'name'


@method_decorator(csrf_protect, name='put')
@method_decorator(csrf_protect, name='patch')
@method_decorator(csrf_protect, name='delete')
class GroupDetail(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a group instance.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    lookup_field = 'name'


@login_required
def change_own_password(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            ldap_user.set_password(form.cleaned_data['password_1'])
            return HttpResponseRedirect(reverse('index'))
    else:
        form = PasswordForm()
    template_values = {'form': form, }
    return render_to_response('penatesserver/change_password.html', template_values, RequestContext(request))


@login_required
def get_user_mobileconfig(request):
    user = get_object_or_404(User, name=request.user.username)
    password = request.GET.get('password', '')
    if not password:
        password = user.read_password()
    password = password or 'password'
    pki = PKI()
    p12_certificates = []
    for (entry, title) in (
            (user.user_certificate_entry, _('User certificate')),
            (user.encipherment_certificate_entry, _('Encipherment certificate')),
            (user.email_certificate_entry, _('Email certificate')),
            (user.signature_certificate_entry, _('Signature certificate')),
    ):
        with tempfile.NamedTemporaryFile() as fd:
            filename = fd.name
        pki.ensure_certificate(entry)
        pki.gen_pkcs12(entry, filename, password=password)
        p12_certificates.append((filename, title))

    def f_scheme(y):
        if y in ('caldav', 'carddav'):
            return 'http'
        return y

    kerberos_prefixes = ['%s%s://%s/' % (f_scheme(x[0]), 's' if x[2] == 'tls' else '', x[1]) for x in
                         Service.objects.filter(scheme__in=['http', 'smtp', 'imap', 'ldap', 'caldav', 'carddav'])
                         .exclude(kerberos_service=None).values_list('scheme', 'hostname', 'encryption')]
    domain_components = settings.PENATES_DOMAIN.split('.')
    domain_components.reverse()
    inverted_domain = '.'.join(domain_components)
    template_values = {
        'domain': settings.PENATES_DOMAIN,
        'inverted_domain': inverted_domain,
        'organization': settings.PENATES_ORGANIZATION,
        'realm': settings.PENATES_REALM,
        'ldap_servers': [],
        'carddav_servers': [],
        'caldav_servers': [],
        'email_servers': [],
        'kerberos_prefixes': kerberos_prefixes,
        'vpn_servers': [],
        'http_proxies': [],
        'password': password,
        'username': user.name,
        'user': user,
        'ldap_base_dn': settings.LDAP_BASE_DN,
        'ca_cert_path': pki.cacrt_path,
        'hosts_crt_path': pki.hosts_crt_path,
        'users_crt_path': pki.users_crt_path,
        'services_crt_path': pki.services_crt_path,
        'p12_certificates': p12_certificates,
    }
    mail_services = {}
    for service in Service.objects.all():
        if service.scheme == 'ldap':
            template_values['ldap_servers'].append(service)
        elif service.scheme == 'carddav':
            template_values['carddav_servers'].append(service)
        elif service.scheme == 'caldav':
            template_values['caldav_servers'].append(service)
        elif service.scheme == 'imap':
            mail_services.setdefault(service.hostname, {})['imap'] = service
        elif service.scheme == 'smtp':
            mail_services.setdefault(service.hostname, {})['smtp'] = service
        elif service.scheme == 'proxy_http':
            template_values['http_proxies'].append(service)

    template_values['email_servers'] = list(mail_services.values())
    response = render_to_response('penatesserver/mobileconfig.xml', template_values, content_type='application/xml')
    for filename, title in p12_certificates:
        os.remove(filename)
    response['Content-Disposition'] = 'attachment; filename=%s.mobileconfig' % request.user.username
    return response
