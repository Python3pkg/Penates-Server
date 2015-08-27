# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import base64
import hashlib
import os
import re
import tempfile

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from django.utils.translation import ugettext as _
import netaddr

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from penatesserver.forms import PasswordForm
from penatesserver.kerb import add_principal_to_keytab, add_principal, principal_exists
from penatesserver.models import Service, Host, User, Group
from penatesserver.pki.constants import COMPUTER, SERVICE, KERBEROS_DC, PRINTER, TIME_SERVER
from penatesserver.pki.service import CertificateEntry, PKI
from penatesserver.powerdns.models import Domain, Record
from penatesserver.serializers import UserSerializer, GroupSerializer
from penatesserver.utils import hostname_from_principal, principal_from_hostname, guess_use_ssl

__author__ = 'flanker'


class CertificateEntryResponse(HttpResponse):
    def __init__(self, entry, **kwargs):
        pki = PKI()
        pki.ensure_certificate(entry)
        content = b''
        # noinspection PyTypeChecker
        with open(entry.key_filename, 'rb') as fd:
            content += fd.read()
        # noinspection PyTypeChecker
        with open(entry.crt_filename, 'rb') as fd:
            content += fd.read()
        # noinspection PyTypeChecker
        with open(entry.ca_filename, 'rb') as fd:
            content += fd.read()
        super(CertificateEntryResponse, self).__init__(content=content, content_type='text/plain', **kwargs)


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
    return CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION, organizationalUnitName=_('Computers'),
                            emailAddress=settings.PENATES_EMAIL_ADDRESS, localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                            stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=COMPUTER)


def index(request):
    template_values = {'protocol': settings.PROTOCOL,
                       'server_name': settings.SERVER_NAME,
                       }
    return render_to_response('penatesserver/index.html', template_values, RequestContext(request))


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
    short_hostname, sep, domain_name = hostname.partition('.')
    domain_name = settings.PENATES_DOMAIN
    long_hostname = '%s.%s' % (short_hostname, domain_name)
    # valid FQDN
    # create Kerberos principal
    principal = principal_from_hostname(long_hostname, settings.PENATES_REALM)
    if principal_exists(principal):
        return HttpResponse('', status=403)
    else:
        add_principal(principal)
    Host.objects.get_or_create(fqdn=long_hostname)
    # create private key, public key, public certificate, public SSH key
    entry = entry_from_hostname(long_hostname)
    pki = PKI()
    pki.ensure_certificate(entry)
    # create DNS records
    domain, created = Domain.objects.get_or_create(name=domain_name)
    remote_addr = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if remote_addr:
        domain.ensure_record(remote_addr, long_hostname)
        domain.update_soa()
        Host.objects.filter(fqdn=long_hostname).update(main_ip_address=remote_addr)
    return KeytabResponse(principal)


def set_dhcp(request, mac_address):
    hostname = hostname_from_principal(request.user.username)
    mac_address = mac_address.replace('-', ':')
    remote_addr = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if remote_addr:
        Host.objects.filter(fqdn=hostname).update(main_ip_address=remote_addr, main_mac_address=mac_address)
    return HttpResponse(status=201)


def get_host_certificate(request):
    entry = entry_from_hostname(hostname_from_principal(request.user.username))
    return CertificateEntryResponse(entry)


def set_ssh_pub(request):
    hostname = hostname_from_principal(request.user.username)
    short_hostname, sep, domain_name = hostname.partition('.')
    domain_name = settings.PENATES_DOMAIN
    long_hostname = '%s.%s' % (short_hostname, domain_name)
    if Host.objects.filter(fqdn=hostname).count() == 0:
        return HttpResponse(status=404)
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
    domain, created = Domain.objects.get_or_create(name=domain_name)
    sha1_value = '%s 1 %s' % (algorithm_code, sha1_hash)
    sha256_value = '%s 2 %s' % (algorithm_code, sha256_hash)
    for value in sha1_value, sha256_value:
        if Record.objects.filter(domain=domain, name=long_hostname, type='SSHFP', content__startswith=value[:4]).count() == 0:
            Record(domain=domain, name=long_hostname, type='SSHFP', content=value, ttl=86400).save()
        else:
            Record.objects.filter(domain=domain, name=long_hostname, type='SSHFP', content__startswith=value[:4]).update(content=value)
    return HttpResponse(status=201)


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


def set_service(request, scheme, hostname, port):
    scheme, use_ssl = guess_use_ssl(scheme)
    srv_field = request.GET.get('srv', None)
    kerberos_service = request.GET.get('keytab', None)
    role = request.GET.get('role', SERVICE)
    protocol = request.GET.get('protocol', 'tcp')
    if protocol not in ('tcp', 'udp', 'socket'):
        return HttpResponse('Invalid protocol: %s' % protocol, status=403, content_type='text/plain')
    description = request.body
    fqdn = hostname_from_principal(request.user.username)
    # a few checks
    if Service.objects.filter(hostname=hostname).exclude(fqdn=fqdn).count() > 0:
        return HttpResponse(status=401, content='%s is already registered' % hostname)
    if role not in (SERVICE, KERBEROS_DC, PRINTER, TIME_SERVER):
        return HttpResponse(status=401, content='Role %s is not allowed' % role)
    if kerberos_service not in ('HTTP', 'XMPP'):
        return HttpResponse(status=401, content='Kerberos service %s is not allowed' % role)
    # Penates service
    service, created = Service.objects.get_or_create(fqdn=fqdn, scheme=scheme, hostname=hostname, port=port, protocol=protocol)
    Service.objects.filter(pk=service.pk).update(kerberos_service=kerberos_service, description=description, dns_srv=srv_field, use_ssl=use_ssl)
    # certificates
    entry = CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION,
                             organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                             localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                             stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=role)
    pki = PKI()
    pki.ensure_certificate(entry)
    # kerberos principal
    principal_name = '%s/%s@%s' % (kerberos_service, fqdn, settings.PENATES_REALM)
    add_principal(principal_name)
    # DNS part
    record_name, sep, domain_name = hostname.partition('.')
    if sep == '.':
        domain, created = Domain.objects.get_or_create(name=domain_name)
        domain.ensure_record(fqdn, hostname)
        domain.set_extra_records(scheme, hostname, port, fqdn, srv_field)
        domain.update_soa()
    return HttpResponse(status=201, content='%s://%s:%s/ created' % (scheme, hostname, port))


def get_service_keytab(request, scheme, hostname, port):
    fqdn = hostname_from_principal(request.user.username)
    protocol = request.GET.get('protocol', 'tcp')
    services = list(Service.objects.filter(fqdn=fqdn, scheme=scheme, hostname=hostname, port=port, protocol=protocol)[0:1])
    if not services:
        return HttpResponse(status=404, content='%s://%s:%s/ unknown' % (scheme, hostname, port))
    service = services[0]
    principal_name = '%s/%s@%s' % (service.kerberos_service, fqdn, settings.PENATES_REALM)
    if not principal_exists(principal_name):
        return HttpResponse(status=404, content='Principal for %s://%s:%s/ undefined' % (scheme, hostname, port))
    return KeytabResponse(principal_name)


def get_service_certificate(request, scheme, hostname, port):
    fqdn = hostname_from_principal(request.user.username)
    role = request.GET.get('role', SERVICE)
    protocol = request.GET.get('protocol', 'tcp')
    services = list(Service.objects.filter(fqdn=fqdn, scheme=scheme, hostname=hostname, port=port, protocol=protocol)[0:1])
    if not services:
        return HttpResponse(status=404, content='%s://%s:%s/ unknown' % (scheme, hostname, port))
    entry = CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION,
                             organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                             localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                             stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=role)
    return CertificateEntryResponse(entry)


def get_dhcpd_conf(request):

    def get_ip_or_none(scheme):
        values = list(Service.objects.filter(scheme=scheme)[0:1])
        if not values:
            return None
        return Record.local_resolve(values[0].fqdn) or values[0].hostname

    def get_ip_list(scheme):
        values = list(Service.objects.filter(scheme=scheme))
        return [Record.local_resolve(x.fqdn) or x.hostname for x in values]

    template_values = {'penates_router': settings.PENATES_ROUTER,
                       'penates_subnet': settings.PENATES_SUBNET,
                       'penates_domain': settings.PENATES_DOMAIN,
                       'hosts': Host.objects.all(),
                       'tftp': get_ip_or_none('tftp'),
                       'dns_list': get_ip_list('dns'),
                       'ntp': get_ip_or_none('ntp'),
                       }
    return render_to_response('dhcpd/dhcpd.conf', template_values, status=200, content_type='text/plain')


class UserList(ListCreateAPIView):
    """
    List all users, or create a new user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'name'


class UserDetail(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a user instance.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'name'


class GroupList(ListCreateAPIView):
    """
    List all groups, or create a new group.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    lookup_field = 'name'


class GroupDetail(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a group instance.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    lookup_field = 'name'


def change_own_password(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            ldap_user.set_password(form.cleaned_data['password_1'])
            return HttpResponseRedirect(reverse('penatesserver.views.index'))
    else:
        form = PasswordForm()
    template_values = {'form': form, }
    return render_to_response('penatesserver/change_password.html', template_values, RequestContext(request))


def get_user_certificate(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    return CertificateEntryResponse(ldap_user.user_certificate_entry)


def get_email_certificate(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    return CertificateEntryResponse(ldap_user.email_certificate_entry)


def get_signature_certificate(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    return CertificateEntryResponse(ldap_user.signature_certificate_entry)


def get_encipherment_certificate(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    return CertificateEntryResponse(ldap_user.encipherment_certificate_entry)
