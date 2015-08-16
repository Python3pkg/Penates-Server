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

from penatesserver.models import Principal
from penatesserver.pki.constants import COMPUTER
from penatesserver.pki.service import CertificateEntry, PKI
from penatesserver.utils import hostname_from_keytab

__author__ = 'flanker'


def index(request):
    template_values = {}
    return render_to_response('penatesserver/index.html', template_values, RequestContext(request))


def get_host_keytab(request, hostname):
    name = 'HOST/%s@%s' % (hostname, settings.PENATES_REALM)
    if list(Principal.objects.filter(name=name)[0:1]):
        return HttpResponse('', status=401)
    Principal(name=name).save()
    with tempfile.NamedTemporaryFile() as fd:
        keytab_filename = fd.name
    p = subprocess.Popen(['kadmin', '-p', '-k', '-t', settings.PENATES_KEYTAB], stdin=subprocess.PIPE)
    p.communicate(('ktadd -k %s %s' % (keytab_filename, name)).encode('utf-8'))
    with open(keytab_filename, 'rb') as fd:
        content = fd.read()
    os.remove(keytab_filename)
    return HttpResponse(content, status=200)


def get_host_certificate(request):
    username = request.user.username
    entry = CertificateEntry(hostname_from_keytab(username), organizationName=settings.PENATES_ORGANIZATION, organizationalUnitName=_('Computers'),
                             emailAddress=settings.PENATES_EMAIL_ADDRESS, localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY,
                             stateOrProvinceName=settings.PENATES_STATE, altNames=[], role=COMPUTER)
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


def register_service(request, protocol, alias, port, kerberos_service=None):
    raise NotImplementedError


def get_service_keytab(request, protocol, alias, port, kerberos_service):
    raise NotImplementedError


def get_service_certificate(request, protocol, alias, port, kerberos_service=None):
    raise NotImplementedError
