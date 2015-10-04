# -*- coding: utf-8 -*-
"""
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
from penatesserver.pki.views import get_host_certificate
from penatesserver.powerdns.management.commands.ensure_domain import Command as EnsureDomain
from penatesserver.management.commands.service import Command as Service
from penatesserver.powerdns.models import Record, Domain
from penatesserver.utils import principal_from_hostname
from penatesserver.views import get_host_keytab, set_dhcp, set_service, set_ssh_pub, get_service_keytab, get_dhcpd_conf

__author__ = 'Matthieu Gallet'


class TestDns(TestCase):
    domain_name = 'test.example.org'
    first_infra_fqdn = 'vm01.%s%s' % (settings.PDNS_INFRA_PREFIX, domain_name)
    first_admin_fqdn = 'vm01.%s%s' % (settings.PDNS_ADMIN_PREFIX, domain_name)
    first_infra_ip_address = '10.19.1.134'
    first_admin_ip_address = '10.19.1.134'
    second_infra_fqdn = 'vm02.%s%s' % (settings.PDNS_INFRA_PREFIX, domain_name)
    second_admin_fqdn = 'vm02.%s%s' % (settings.PDNS_ADMIN_PREFIX, domain_name)
    second_infra_ip_address = '10.19.1.130'
    second_admin_ip_address = '10.8.0.130'

    @classmethod
    def setUpClass(cls):
        TestCase.setUpClass()
        pki = PKI()
        pki.initialize()
        entry = CertificateEntry(cls.domain_name, organizationalUnitName='certificates', emailAddress=settings.PENATES_EMAIL_ADDRESS,
                                 localityName=settings.PENATES_LOCALITY, countryName=settings.PENATES_COUNTRY, stateOrProvinceName=settings.PENATES_STATE,
                                 altNames=[], role=CA)
        pki.ensure_ca(entry)

    def request(self, client_address=None, client_fqdn=None, request_body='', **kwargs):
        request = HttpRequest()
        principal = principal_from_hostname(client_fqdn, settings.PDNS_INFRA_PREFIX + settings.PENATES_REALM)
        request.GET = kwargs
        request.META = {'HTTP_X_FORWARDED_FOR': client_address}
        user, c = DjangoUser.objects.get_or_create(username=principal)
        request.user = user
        request._body = request_body
        return request
    
    def first_request(self, request_body='', **kwargs):
        return self.request(client_address=self.first_infra_ip_address, client_fqdn=self.first_infra_fqdn, request_body=request_body, **kwargs)
    
    def second_request(self, request_body='', **kwargs):
        return self.request(client_address=self.second_infra_ip_address, client_fqdn=self.second_infra_fqdn, request_body=request_body, **kwargs)

    def test_complete_scenario(self):
        cmd = EnsureDomain()
        cmd.handle(domain=self.domain_name)
        hostname = 'directory01.%s' % self.domain_name
        self.call_service(scheme='ldaps', hostname=hostname, port=636, fqdn=self.first_infra_fqdn, encryption='tls')
        self.call_service(scheme='krb', hostname=hostname, port=88, fqdn=self.first_infra_fqdn, srv='tcp/kerberos')
        self.call_service(scheme='krb', hostname=hostname, port=88, fqdn=self.first_infra_fqdn, srv='tcp/kerberos', protocol='udp')
        self.call_service(scheme='http', hostname=hostname, port=443, fqdn=self.first_infra_fqdn, encryption='tls')
        self.call_service(scheme='dns', hostname=hostname, port=53, fqdn=self.first_infra_fqdn, protocol='udp')
        self.assertEqual(1, Record.objects.filter(name='_636._tcp.%s' % hostname, type='TLSA').count())
        self.assertEqual(1, Record.objects.filter(name='_88._tcp.%s' % hostname, type='TLSA').count())
        self.assertEqual(1, Record.objects.filter(name='_88._udp.%s' % hostname, type='TLSA').count())
        self.assertEqual(1, Record.objects.filter(name='_443._tcp.%s' % hostname, type='TLSA').count())

        response = get_host_keytab(self.first_request(ip_address=self.first_admin_ip_address), self.first_infra_fqdn)
        principal = principal_from_hostname(self.first_infra_fqdn, settings.PENATES_REALM)
        self.assertTrue(principal in text_type(response.content))

        response = get_host_keytab(self.second_request(ip_address=self.second_admin_ip_address), self.second_infra_fqdn)
        principal = principal_from_hostname(self.second_infra_fqdn, settings.PENATES_REALM)
        self.assertTrue(principal in text_type(response.content))

        domain_names = {x.name for x in Domain.objects.all()}
        for domain_name in [self.domain_name, '%s%s' % (settings.PDNS_ADMIN_PREFIX, self.domain_name), '%s%s' % (settings.PDNS_INFRA_PREFIX, self.domain_name),
                            '1.19.10.in-addr.arpa', '0.8.10.in-addr.arpa', ]:
            self.assertTrue(domain_name in domain_names)

        set_dhcp(self.first_request(ip_address=self.first_admin_ip_address, mac_address='5E:FF:56:A2:AF:15'), '5E:FF:56:A2:AF:15')
        self.assertEqual(Record.objects.filter(name=self.first_infra_fqdn, type='A', content=self.first_infra_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.first_admin_fqdn, type='A', content=self.first_admin_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.second_infra_fqdn, type='A', content=self.second_infra_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.second_admin_fqdn, type='A', content=self.second_admin_ip_address).count(), 1)

        set_dhcp(self.second_request(ip_address=self.second_admin_ip_address, mac_address='88:FF:56:A2:AF:15'), '90:FF:56:A2:AF:15')
        self.assertEqual(Record.objects.filter(name=self.first_infra_fqdn, type='A', content=self.first_infra_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.first_admin_fqdn, type='A', content=self.first_admin_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.second_infra_fqdn, type='A', content=self.second_infra_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.second_admin_fqdn, type='A', content=self.second_admin_ip_address).count(), 1)

        response = set_service(self.first_request(keytab='host', srv='tcp/ssh'), 'ssh', self.first_admin_fqdn, '22')
        self.assertEqual('ssh://%s:22/ created' % self.first_admin_fqdn, response.content)
        self.assertEqual(Record.objects.filter(name=self.first_infra_fqdn, type='A', content=self.first_infra_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.first_admin_fqdn, type='CNAME', content=self.first_infra_fqdn).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.second_infra_fqdn, type='A', content=self.second_infra_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.second_admin_fqdn, type='A', content=self.second_admin_ip_address).count(), 1)

        response = set_service(self.second_request(keytab='host', srv='tcp/ssh'), 'ssh', self.second_admin_fqdn, '22')
        self.assertEqual('ssh://%s:22/ created' % self.second_admin_fqdn, response.content)
        self.assertEqual(Record.objects.filter(name=self.first_infra_fqdn, type='A', content=self.first_infra_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.first_admin_fqdn, type='CNAME', content=self.first_infra_fqdn).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.second_infra_fqdn, type='A', content=self.second_infra_ip_address).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.second_admin_fqdn, type='A', content=self.second_admin_ip_address).count(), 1)

        response = get_service_keytab(self.first_request(protocol='tcp'), 'ssh', self.first_admin_fqdn, '22')
        self.assertTrue('host/%s@%s' % (self.first_infra_fqdn, settings.PENATES_REALM) in text_type(response.content))

        response = get_service_keytab(self.second_request(protocol='tcp'), 'ssh', self.second_admin_fqdn, '22')
        self.assertTrue('host/%s@%s' % (self.second_admin_fqdn, settings.PENATES_REALM) in text_type(response.content))

        body = "ssh-rsa QkJCQnozcVZRSTlNYTFIYw== flanker@%s" % self.first_infra_fqdn
        response = set_ssh_pub(self.first_request(request_body=body))
        self.assertEqual(201, response.status_code)
        body = "ssh-rsa RkJCQnozcVZRSTlNYTFIYw== flanker@%s" % self.second_infra_fqdn
        response = set_ssh_pub(self.second_request(request_body=body))
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, Record.objects.filter(name=self.first_admin_fqdn, type='SSHFP', content='1 1 915984d4f71be43b49154b61c786d1a092e49a4d').count())
        self.assertEqual(4, Record.objects.filter(type='SSHFP').count())

        response = get_host_certificate(self.first_request())
        self.assertTrue('-----BEGIN RSA PRIVATE KEY-----' in text_type(response.content))
        self.assertTrue('-----END CERTIFICATE-----' in text_type(response.content))

        response = get_host_certificate(self.second_request())
        self.assertTrue('-----BEGIN RSA PRIVATE KEY-----' in text_type(response.content))
        self.assertTrue('-----END CERTIFICATE-----' in text_type(response.content))

        response = get_dhcpd_conf(self.first_request())
        print(response.content)

        for record in Record.objects.all():
            print(repr(record))

    def call_service(self, **kwargs):
        cmd = Service()
        defaults = {'fqdn': None, 'kerberos_service': None, 'srv': None, 'protocol': 'tcp', 'description': 'description', 'cert': None,
                    'key': None, 'pubkey': None, 'ssh': None, 'pubssh': None, 'ca': None, 'keytab': None, 'role': 'Service', 'encryption': 'none', }
        defaults.update(kwargs)
        cmd.handle(**defaults)
