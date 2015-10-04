# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import subprocess

from django.http import HttpRequest
from django.test import TestCase
from django.conf import settings
from django.utils.six import text_type

from penatesserver.models import DjangoUser
from penatesserver.pki.constants import CA
from penatesserver.pki.service import PKI, CertificateEntry
from penatesserver.pki.views import get_host_certificate, get_service_certificate
from penatesserver.powerdns.management.commands.ensure_domain import Command as EnsureDomain
from penatesserver.management.commands.service import Command as Service
from penatesserver.powerdns.models import Record, Domain
from penatesserver.utils import principal_from_hostname
from penatesserver.views import get_host_keytab, set_dhcp, set_service, set_ssh_pub, get_service_keytab, get_dhcpd_conf

__author__ = 'Matthieu Gallet'


class TestDns(TestCase):
    domain_name = 'test.example.org'
    infra_fqdn_1 = 'vm01.%s%s' % (settings.PDNS_INFRA_PREFIX, domain_name)
    admin_fqdn_1 = 'vm01.%s%s' % (settings.PDNS_ADMIN_PREFIX, domain_name)
    infra_ip_address_1 = '10.19.1.134'
    admin_ip_address_1 = '10.19.1.134'
    infra_fqdn_2 = 'vm02.%s%s' % (settings.PDNS_INFRA_PREFIX, domain_name)
    admin_fqdn_2 = 'vm02.%s%s' % (settings.PDNS_ADMIN_PREFIX, domain_name)
    infra_ip_address_2 = '10.19.1.130'
    admin_ip_address_2 = '10.8.0.130'
    service_1_fqdn = 'srv01.%s' % domain_name
    service_2_fqdn = 'srv02.%s' % domain_name
    service_3_fqdn = 'srv03.%s' % domain_name
    service_4_fqdn = 'srv04.%s' % domain_name

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
    
    def request_1(self, request_body='', **kwargs):
        return self.request(client_address=self.infra_ip_address_1, client_fqdn=self.infra_fqdn_1, request_body=request_body, **kwargs)
    
    def request_2(self, request_body='', **kwargs):
        return self.request(client_address=self.infra_ip_address_2, client_fqdn=self.infra_fqdn_2, request_body=request_body, **kwargs)

    def test_complete_scenario(self):
        cmd = EnsureDomain()
        cmd.handle(domain=self.domain_name)
        hostname = 'directory01.%s' % self.domain_name
        self.call_service(scheme='ldaps', hostname=hostname, port=636, fqdn=self.infra_fqdn_1, encryption='tls')
        self.call_service(scheme='krb', hostname=hostname, port=88, fqdn=self.infra_fqdn_1, srv='tcp/kerberos')
        self.call_service(scheme='krb', hostname=hostname, port=88, fqdn=self.infra_fqdn_1, srv='tcp/kerberos', protocol='udp')
        self.call_service(scheme='http', hostname=hostname, port=443, fqdn=self.infra_fqdn_1, encryption='tls')
        self.call_service(scheme='dns', hostname=hostname, port=53, fqdn=self.infra_fqdn_1, protocol='udp')
        self.assertEqual(1, Record.objects.filter(name='_636._tcp.%s' % hostname, type='TLSA').count())
        self.assertEqual(1, Record.objects.filter(name='_88._tcp.%s' % hostname, type='TLSA').count())
        self.assertEqual(1, Record.objects.filter(name='_88._udp.%s' % hostname, type='TLSA').count())
        self.assertEqual(1, Record.objects.filter(name='_443._tcp.%s' % hostname, type='TLSA').count())

        response = get_host_keytab(self.request_1(ip_address=self.admin_ip_address_1), self.infra_fqdn_1)
        principal = principal_from_hostname(self.infra_fqdn_1, settings.PENATES_REALM)
        self.assertTrue(principal in text_type(response.content))

        response = get_host_keytab(self.request_2(ip_address=self.admin_ip_address_2), self.infra_fqdn_2)
        principal = principal_from_hostname(self.infra_fqdn_2, settings.PENATES_REALM)
        self.assertTrue(principal in text_type(response.content))

        domain_names = {x.name for x in Domain.objects.all()}
        for domain_name in [self.domain_name, '%s%s' % (settings.PDNS_ADMIN_PREFIX, self.domain_name), '%s%s' % (settings.PDNS_INFRA_PREFIX, self.domain_name),
                            '1.19.10.in-addr.arpa', '0.8.10.in-addr.arpa', ]:
            self.assertTrue(domain_name in domain_names)

        set_dhcp(self.request_1(ip_address=self.admin_ip_address_1, mac_address='5E:FF:56:A2:AF:15'), '5E:FF:56:A2:AF:15')
        self.assertEqual(Record.objects.filter(name=self.infra_fqdn_1, type='A', content=self.infra_ip_address_1).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.admin_fqdn_1, type='A', content=self.admin_ip_address_1).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.infra_fqdn_2, type='A', content=self.infra_ip_address_2).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.admin_fqdn_2, type='A', content=self.admin_ip_address_2).count(), 1)

        set_dhcp(self.request_2(ip_address=self.admin_ip_address_2, mac_address='88:FF:56:A2:AF:15'), '90:FF:56:A2:AF:15')
        self.assertEqual(Record.objects.filter(name=self.infra_fqdn_1, type='A', content=self.infra_ip_address_1).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.admin_fqdn_1, type='A', content=self.admin_ip_address_1).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.infra_fqdn_2, type='A', content=self.infra_ip_address_2).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.admin_fqdn_2, type='A', content=self.admin_ip_address_2).count(), 1)

        response = set_service(self.request_1(keytab='host', srv='tcp/ssh'), 'ssh', self.admin_fqdn_1, '22')
        self.assertEqual('ssh://%s:22/ created' % self.admin_fqdn_1, response.content)
        self.assertEqual(Record.objects.filter(name=self.infra_fqdn_1, type='A', content=self.infra_ip_address_1).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.admin_fqdn_1, type='CNAME', content=self.infra_fqdn_1).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.infra_fqdn_2, type='A', content=self.infra_ip_address_2).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.admin_fqdn_2, type='A', content=self.admin_ip_address_2).count(), 1)

        response = set_service(self.request_2(keytab='host', srv='tcp/ssh'), 'ssh', self.admin_fqdn_2, '22')
        self.assertEqual('ssh://%s:22/ created' % self.admin_fqdn_2, response.content)
        self.assertEqual(Record.objects.filter(name=self.infra_fqdn_1, type='A', content=self.infra_ip_address_1).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.admin_fqdn_1, type='CNAME', content=self.infra_fqdn_1).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.infra_fqdn_2, type='A', content=self.infra_ip_address_2).count(), 1)
        self.assertEqual(Record.objects.filter(name=self.admin_fqdn_2, type='A', content=self.admin_ip_address_2).count(), 1)

        response = get_service_keytab(self.request_1(protocol='tcp'), 'ssh', self.admin_fqdn_1, '22')
        self.assertTrue('host/%s@%s' % (self.infra_fqdn_1, settings.PENATES_REALM) in text_type(response.content))

        response = get_service_keytab(self.request_2(protocol='tcp'), 'ssh', self.admin_fqdn_2, '22')
        self.assertTrue('host/%s@%s' % (self.admin_fqdn_2, settings.PENATES_REALM) in text_type(response.content))

        body = "ssh-rsa QkJCQnozcVZRSTlNYTFIYw== flanker@%s" % self.infra_fqdn_1
        response = set_ssh_pub(self.request_1(request_body=body))
        self.assertEqual(201, response.status_code)
        body = "ssh-rsa RkJCQnozcVZRSTlNYTFIYw== flanker@%s" % self.infra_fqdn_2
        response = set_ssh_pub(self.request_2(request_body=body))
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, Record.objects.filter(name=self.admin_fqdn_1, type='SSHFP', content='1 1 915984d4f71be43b49154b61c786d1a092e49a4d').count())
        self.assertEqual(4, Record.objects.filter(type='SSHFP').count())

        response = get_host_certificate(self.request_1())
        self.assertTrue('-----BEGIN RSA PRIVATE KEY-----' in text_type(response.content))
        self.check_certificate(response.content, self.infra_fqdn_1, 'Computers')

        response = get_host_certificate(self.request_2())
        self.assertTrue('-----BEGIN RSA PRIVATE KEY-----' in text_type(response.content))
        self.check_certificate(response.content, self.infra_fqdn_2, 'Computers')

        get_dhcpd_conf(self.request_1())

        response = set_service(self.request_1(encryption='tls'), 'syslog', self.service_1_fqdn, '514')
        self.assertEqual('syslog://%s:514/ created' % self.service_1_fqdn, response.content)
        self.assertEqual(1, Record.objects.filter(name=self.service_1_fqdn, content=self.infra_fqdn_1, type='CNAME').count())
        response = get_service_certificate(self.request_1(), 'syslog', self.service_1_fqdn, '514')
        self.check_certificate(response.content, self.service_1_fqdn, 'Services')

        response = set_service(self.request_2(encryption='tls'), 'syslog', self.service_2_fqdn, '514')
        self.assertEqual('syslog://%s:514/ created' % self.service_2_fqdn, response.content)
        self.assertEqual(1, Record.objects.filter(name=self.service_2_fqdn, content=self.infra_fqdn_2, type='CNAME').count())
        response = get_service_certificate(self.request_2(), 'syslog', self.service_2_fqdn, '514')
        self.check_certificate(response.content, self.service_2_fqdn, 'Services')

        response = set_service(self.request_1(role='Service1024', encryption='tls'), 'dkim', self.service_3_fqdn, '10026')
        self.assertEqual('dkim://%s:10026/ created' % self.service_3_fqdn, response.content)
        self.assertEqual(1, Record.objects.filter(name=self.service_3_fqdn, content=self.infra_fqdn_1, type='CNAME').count())
        self.assertEqual(1, Record.objects.filter(name='%s._domainkey.%s' % (self.service_3_fqdn.partition('.')[0], settings.PENATES_DOMAIN), type='TXT').count())

        response = set_service(self.request_1(keytab='smtp', srv='smtp'), 'smtp', self.service_3_fqdn, '25')
        self.assertEqual('smtp://%s:25/ created' % self.service_3_fqdn, response.content)
        self.assertEqual(1, Record.objects.filter(name=settings.PENATES_DOMAIN, type='MX', content=self.service_3_fqdn).count())

        response = set_service(self.request_2(keytab='smtp', srv='smtp'), 'smtp', self.service_4_fqdn, '25')
        self.assertEqual('smtp://%s:25/ created' % self.service_4_fqdn, response.content)
        self.assertEqual(1, Record.objects.filter(name=self.service_4_fqdn, content=self.infra_fqdn_2, type='CNAME').count())
        self.assertEqual(1, Record.objects.filter(name=settings.PENATES_DOMAIN, type='MX', content=self.service_3_fqdn).count())
        response = set_service(self.request_2(role='Service1024', encryption='tls'), 'dkim', self.service_4_fqdn, '10026')
        self.assertEqual('dkim://%s:10026/ created' % self.service_4_fqdn, response.content)
        self.assertEqual(1, Record.objects.filter(name=self.service_4_fqdn, content=self.infra_fqdn_2, type='CNAME').count())
        self.assertEqual(1, Record.objects.filter(name='%s._domainkey.%s' % (self.service_4_fqdn.partition('.')[0], settings.PENATES_DOMAIN), type='TXT').count())

        for record in Record.objects.all():
            print(repr(record))

    def check_certificate(self, content, fqdn, role):
        p = subprocess.Popen(['openssl', 'x509', '-subject', '-noout'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = p.communicate(content.encode('utf-8'))
        expected = "subject= /CN=%s/emailAddress=admin@%s/O=%s/OU=%s/L=%s/ST=%s/C=%s\n" % (
            fqdn, settings.PENATES_DOMAIN, settings.PENATES_ORGANIZATION, role,
            settings.PENATES_LOCALITY, settings.PENATES_STATE, settings.PENATES_COUNTRY
        )
        self.assertEqual(expected.replace('î', 'Î'), stdout.decode('latin1'))

    def call_service(self, **kwargs):
        cmd = Service()
        defaults = {'fqdn': None, 'kerberos_service': None, 'srv': None, 'protocol': 'tcp', 'description': 'description', 'cert': None,
                    'key': None, 'pubkey': None, 'ssh': None, 'pubssh': None, 'ca': None, 'keytab': None, 'role': 'Service', 'encryption': 'none', }
        defaults.update(kwargs)
        cmd.handle(**defaults)
