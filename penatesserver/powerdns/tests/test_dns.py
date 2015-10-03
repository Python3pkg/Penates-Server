# -*- coding: utf-8 -*-
"""
k5start -q -f /etc/host.keytab -U -- curl --anyauth -u : https://{{ penates_directory_fqdn }}/auth/set_dhcp/{{ primary_mac_address.stdout }}/?admin_mac_address={{ network_config['admin'][1] }}&admin_ip_address={{ network_config['admin'][2] }}
k5start -q -f /etc/host.keytab -U -- curl --anyauth -u : https://{{ penates_directory_fqdn }}/auth/set_service/ssh/{{ ansible_nodename }}.{{ penates_domain }}/22/?keytab=host
k5start -q -f /etc/host.keytab -U -- curl -o /etc/krb5.keytab --anyauth -u : https://{{ penates_directory_fqdn }}/auth/get_service_keytab/ssh/{{ ansible_nodename }}.{{ penates_domain }}/22/
k5start -q -f /etc/host.keytab -U -- curl -o /etc/ssl/private/host.pem --anyauth -u : https://{{ penates_directory_fqdn }}/auth/get_host_certificate/
k5start -q -f /etc/host.keytab -U -- curl --data-binary @/etc/ssh/ssh_host_ecdsa_key.pub --anyauth -u : https://{{ penates_directory_fqdn }}/auth/set_ssh_pub/
k5start -q -f /etc/host.keytab -U -- curl --anyauth -u : -o /etc/dhcp/dhcpd.conf https://{{ penates_directory_fqdn }}/auth/conf/dhcpd.conf
‚‚‚
"""
from __future__ import unicode_literals

from django.http import HttpRequest
from django.test import TestCase

from django.conf import settings
from django.utils.six import text_type

from penatesserver.models import DjangoUser
from penatesserver.pki.constants import CA
from penatesserver.pki.service import PKI, CertificateEntry
from penatesserver.powerdns.management.commands.ensure_domain import Command as EnsureDomain
from penatesserver.management.commands.service import Command as Service
from penatesserver.powerdns.models import Record, Domain
from penatesserver.subnets import get_subnets
from penatesserver.utils import principal_from_hostname
from penatesserver.views import get_host_keytab

__author__ = 'Matthieu Gallet'


class TestDns(TestCase):
    domain_name = 'test.example.org'
    fqdn = 'vm01.%s%s' % (settings.PDNS_INFRA_PREFIX, domain_name)

    @classmethod
    def setUpClass(cls):
        TestCase.setUpClass()
        pki = PKI()
        pki.initialize()
        entry = CertificateEntry(cls.domain_name, organizationalUnitName='certificates', emailAddress=settings.PENATES_EMAIL_ADDRESS,
                                 localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY, stateOrProvinceName=settings.PENATES_STATE,
                                 altNames=[], role=CA)
        pki.ensure_ca(entry)

    def request(self, client_address='10.19.1.134', **kwargs):
        request = HttpRequest()
        principal = principal_from_hostname(self.fqdn, settings.PDNS_INFRA_PREFIX + settings.PENATES_REALM)
        request.GET = kwargs
        request.META = {'HTTP_X_FORWARDED_FOR': client_address}
        user, c = DjangoUser.objects.get_or_create(username=principal)
        request.user = user
        return request

    def test_complete_scenario(self):
        cmd = EnsureDomain()
        cmd.handle(domain=self.domain_name)
        self.call_service(scheme='ldaps', hostname='directory01.%s' % self.domain_name, port=636, fqdn=self.fqdn, encryption='tls')
        self.call_service(scheme='krb', hostname='directory01.%s' % self.domain_name, port=88, fqdn=self.fqdn, srv='tcp/kerberos')
        self.call_service(scheme='krb', hostname='directory01.%s' % self.domain_name, port=88, fqdn=self.fqdn, srv='tcp/kerberos', protocol='udp')
        self.call_service(scheme='http', hostname='directory01.%s' % self.domain_name, port=443, fqdn=self.fqdn, encryption='tls')
        self.call_service(scheme='dns', hostname='directory01.%s' % self.domain_name, port=53, fqdn=self.fqdn, protocol='udp')
        host_keytab_response = get_host_keytab(self.request(ip_address='10.19.1.134'), self.fqdn)
        principal = principal_from_hostname(self.fqdn, settings.PENATES_REALM)
        self.assertTrue(principal in text_type(host_keytab_response.content))

        fqdn = 'client.%s%s' % (settings.PDNS_INFRA_PREFIX, self.domain_name)
        host_keytab_response = get_host_keytab(self.request(client_address='10.19.1.130', ip_address='10.8.0.130'), fqdn)
        principal = principal_from_hostname(fqdn, settings.PENATES_REALM)
        self.assertTrue(principal in text_type(host_keytab_response.content))

        domain_names = {x.name for x in Domain.objects.all()}
        for domain_name in [self.domain_name, '%s%s' % (settings.PDNS_ADMIN_PREFIX, self.domain_name), '%s%s' % (settings.PDNS_INFRA_PREFIX, self.domain_name),
                            '1.19.10.in-addr.arpa', '0.8.10.in-addr.arpa', ]:
            self.assertTrue(domain_name in domain_names)
        for record in Record.objects.all():
            print(repr(record))

    def call_service(self, **kwargs):
        cmd = Service()
        defaults = {'fqdn': None, 'kerberos_service': None, 'srv': None, 'protocol': 'tcp', 'description': 'description', 'cert': None,
                    'key': None, 'pubkey': None, 'ssh': None, 'pubssh': None, 'ca': None, 'keytab': None, 'role': None, 'encryption': 'none', }
        defaults.update(kwargs)
        cmd.handle(**defaults)
