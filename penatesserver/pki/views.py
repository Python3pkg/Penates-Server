# -*- coding: utf-8 -*-
from __future__ import unicode_literals, with_statement, print_function

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from penatesserver.models import User, Service
from penatesserver.pki.constants import SERVICE_1024, PRINTER, KERBEROS_DC, SERVICE, TIME_SERVER
from penatesserver.pki.service import PKI, CertificateEntry
from penatesserver.powerdns.models import Domain
from penatesserver.utils import hostname_from_principal
from penatesserver.views import entry_from_hostname, admin_entry_from_hostname

__author__ = 'Matthieu Gallet'


class CertificateEntryResponse(HttpResponse):
    def __init__(self, entry, ensure_entry=True, **kwargs):
        pki = PKI()
        if ensure_entry:
            pki.ensure_certificate(entry)
        content = b''
        # noinspection PyTypeChecker
        with open(entry.key_filename, 'rb') as fd:
            content += fd.read()
        # noinspection PyTypeChecker
        with open(entry.crt_filename, 'rb') as fd:
            content += fd.read()
        ca_crt_path, ca_key_path = pki.get_subca_infos(entry)
        # noinspection PyTypeChecker
        with open(ca_crt_path, 'rb') as fd:
            content += fd.read()
        # noinspection PyTypeChecker
        with open(entry.ca_filename, 'rb') as fd:
            content += fd.read()
        super(CertificateEntryResponse, self).__init__(content=content, content_type='text/plain', **kwargs)


@login_required
def get_host_certificate(request):
    entry = entry_from_hostname(hostname_from_principal(request.user.username))
    return CertificateEntryResponse(entry)


@login_required
def get_admin_certificate(request):
    hostname = hostname_from_principal(request.user.username)
    hostname = '%s.%s%s' % (hostname.partition('.')[0], settings.PDNS_ADMIN_PREFIX, settings.PENATES_DOMAIN)
    entry = admin_entry_from_hostname(hostname)
    return CertificateEntryResponse(entry)


@login_required
def get_service_certificate(request, scheme, hostname, port):
    fqdn = hostname_from_principal(request.user.username)
    role = request.GET.get('role', SERVICE)
    protocol = request.GET.get('protocol', 'tcp')
    port = int(port)
    services = list(Service.objects.filter(fqdn=fqdn, scheme=scheme, hostname=hostname, port=port, protocol=protocol)[0:1])
    if not services:
        return HttpResponse(status=404, content='%s://%s:%s/ unknown' % (scheme, hostname, port))
    if role not in (SERVICE, KERBEROS_DC, PRINTER, TIME_SERVER, SERVICE_1024):
        return HttpResponse(status=401, content='Role %s is not allowed' % role)
    entry = CertificateEntry(hostname, organizationName=settings.PENATES_ORGANIZATION,
                             organizationalUnitName=_('Services'), emailAddress=settings.PENATES_EMAIL_ADDRESS,
                             localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                             stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=role)
    pki = PKI()
    pki.ensure_certificate(entry)
    record_name, sep, domain_name = hostname.partition('.')
    domain = Domain.objects.get(name=domain_name)
    domain.set_certificate_records(entry, protocol, hostname, port)
    return CertificateEntryResponse(entry)


def get_crl(request):
    pki = PKI()
    pki.ensure_crl()
    # noinspection PyTypeChecker
    with open(pki.cacrl_path, 'rb') as fd:
        content = fd.read()
    return HttpResponse(content, content_type='text/plain')


def get_ca_certificate(request, kind='ca'):
    pki = PKI()
    if kind == 'ca':
        path = pki.cacrt_path
    elif kind == 'users':
        path = pki.users_crt_path
    elif kind == 'hosts':
        path = pki.hosts_crt_path
    elif kind == 'services':
        path = pki.services_crt_path
    else:
        raise PermissionDenied
    # noinspection PyTypeChecker
    with open(path, 'rb') as fd:
        content = fd.read()
    return HttpResponse(content, content_type='text/plain')


@login_required
def get_user_certificate(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    return CertificateEntryResponse(ldap_user.user_certificate_entry)


@login_required
def get_email_certificate(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    return CertificateEntryResponse(ldap_user.email_certificate_entry)


@login_required
def get_signature_certificate(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    return CertificateEntryResponse(ldap_user.signature_certificate_entry)


@login_required
def get_encipherment_certificate(request):
    ldap_user = get_object_or_404(User, name=request.user.username)
    return CertificateEntryResponse(ldap_user.encipherment_certificate_entry)
