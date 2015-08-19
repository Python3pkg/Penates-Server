# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import tempfile
import subprocess

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response

from django.template import RequestContext

from django.utils.translation import ugettext as _

from penatesserver.models import Principal, DhcpRecord, Service, DhcpSubnet
from penatesserver.pki.constants import COMPUTER, SERVICE, KERBEROS_DC, PRINTER, TIME_SERVER
from penatesserver.pki.service import CertificateEntry, PKI
from penatesserver.powerdns.models import Domain
from penatesserver.utils import hostname_from_principal, principal_from_hostname

__author__ = 'flanker'


def entry_from_hostname(hostname):
    return CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION, organizationalUnitName=_('Computers'),
                            emailAddress=settings.PENATES_EMAIL_ADDRESS, localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                            stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=COMPUTER)


def get_keytab(principal):
    # create keytab
    with tempfile.NamedTemporaryFile() as fd:
        keytab_filename = fd.name
    p = subprocess.Popen(['kadmin', '-p', settings.PENATES_PRINCIPAL, '-k', '-t', settings.PENATES_KEYTAB, '-q', 'ktadd -k %s %s' % (keytab_filename, principal)], stdout=subprocess.PIPE)
    p.communicate()
    with open(keytab_filename, 'rb') as fd:
        keytab_content = bytes(fd.read())
    os.remove(keytab_filename)
    return keytab_content


def index(request):
    template_values = {}
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
    if list(Principal.objects.filter(name=principal)[0:1]):
        return HttpResponse('', status=401)
    else:
        Principal(name=principal).save()

    # create private key, public key, public certificate, public SSH key
    entry = entry_from_hostname(long_hostname)
    pki = PKI()
    pki.ensure_certificate(entry)
    # create DNS records
    domain, created = Domain.objects.get_or_create(name=domain_name)
    remote_addr = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if remote_addr:
        domain.ensure_record(remote_addr, long_hostname, ssh_sha1_fingerprint=entry.sshfp_sha1, ssh_sha256_fingerprint=entry.sshfp_sha256)
        domain.update_soa()
    keytab_content = get_keytab(principal)

    return HttpResponse(keytab_content, status=200, content_type='application/octet-stream')


def set_dhcp(request, mac_address, ip_address):
    hostname = hostname_from_principal(request.user.username)
    name = mac_address.replace(':', '_')
    if DhcpRecord.objects.filter(name=name).count() > 0:
        return HttpResponse('%s is already registered' % mac_address, status=401)
    DhcpRecord(name=name, hw_address='ethernet %s', options=['fixed-address %s' % ip_address, 'host-name %s' % hostname, ]).save()
    return HttpResponse(status=201)


def get_host_certificate(request):
    entry = entry_from_hostname(hostname_from_principal(request.user.username))
    pki = PKI()
    pki.ensure_certificate(entry)
    content = b''
    with open(entry.key_filename, 'rb') as fd:
        content += fd.read()
    with open(entry.crt_filename, 'rb') as fd:
        content += fd.read()
    with open(entry.ca_filename, 'rb') as fd:
        content += fd.read()
    return HttpResponse(content, status=200)


def get_ssh_pub(request):
    entry = entry_from_hostname(hostname_from_principal(request.user.username))
    pki = PKI()
    pki.ensure_certificate(entry)
    with open(entry.ssh_filename, 'rb') as fd:
        content = fd.read()
    return HttpResponse(content, status=200)


def set_service(request, protocol, hostname, port):
    srv_field = request.GET.get('srv', None)
    kerberos_service = request.GET.get('keytab', None)
    role = request.GET.get('role', SERVICE)
    subnets = request.GET.getlist('subnet', [])
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
    service, created = Service.objects.get_or_create(fqdn=fqdn, protocol=protocol, hostname=hostname, port=port)
    Service.objects.filter(pk=service.pk).update(kerberos_service=kerberos_service, description=description, dns_srv=srv_field)
    # certificates
    entry = CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION,
                             organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                             localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                             stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=role)
    pki = PKI()
    pki.ensure_certificate(entry)
    # kerberos principal
    principal_name = '%s/%s@%s' % (kerberos_service, fqdn, settings.PENATES_REALM)
    if not list(Principal.objects.filter(name=principal_name)[0:1]):
        Principal(name=principal_name).save()
    # DNS part
    record_name, sep, domain_name = hostname.partition('.')
    if sep == '.':
        domain, created = Domain.objects.get_or_create(name=domain_name)
        domain.ensure_record(fqdn, hostname)
        domain.set_extra_records(protocol, hostname, port, fqdn, srv_field)
        domain.update_soa()
    for subnet in DhcpSubnet.objects.filter(name__in=subnets):
        subnet.set_extra_records(protocol, hostname, port, fqdn, srv_field)
        subnet.save()
    return HttpResponse(status=201, content='%s://%s:%s/ created' % (protocol, hostname, port))


def get_service_keytab(request, protocol, alias, port, kerberos_service):
    raise NotImplementedError


def get_service_certificate(request, protocol, alias, port, kerberos_service=None):
    raise NotImplementedError
