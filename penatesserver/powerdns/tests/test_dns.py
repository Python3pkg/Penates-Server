# -*- coding: utf-8 -*-
"""
penatesserver-manage ensure_domain {{ penates_domain }}
penatesserver-manage service ldaps {{ auth_fqdn }} 636 --fqdn {{ penates_directory_hostname }} --description "Main LDAP server" --cert /etc/ldap/slapd.d/{{ auth_fqdn }}.crt --key /etc/ldap/slapd.d/{{ auth_fqdn }}.key --encryption=tls
penatesserver-manage ensure_domain {{ penates_domain }}
penatesserver-manage service ldaps {{ auth_fqdn }} 636 --fqdn {{ penates_directory_hostname }} --description "Main LDAP server" --cert /etc/ldap/slapd.d/{{ auth_fqdn }}.crt --key /etc/ldap/slapd.d/{{ auth_fqdn }}.key --encryption=tls
penatesserver-manage service krb {{ auth_fqdn }} 88 --role "Kerberos DC" --fqdn {{ penates_directory_hostname }} --description "Main Kerberos server" --cert /var/lib/heimdal-kdc/{{ auth_fqdn }}.crt --key /var/lib/heimdal-kdc/{{ auth_fqdn }}.key --srv tcp/kerberos
penatesserver-manage service krb {{ auth_fqdn }} 88 --role "Kerberos DC" --fqdn {{ penates_directory_hostname }} --description "Main Kerberos server" --protocol udp --srv tcp/kerberos
penatesserver-manage service http {{ auth_fqdn }} 443 --role "Service" --fqdn {{ penates_directory_hostname }} --description "Penates Webservices" --kerberos_service HTTP --keytab /etc/apache2/http.keytab --cert /etc/apache2/{{ auth_fqdn }}.pem --key /etc/apache2/{{ auth_fqdn }}.pem --ca /etc/apache2/{{ auth_fqdn }}.pem --encryption=tls
penatesserver-manage service dns {{ auth_fqdn }} 53 --role "Service" --fqdn {{ penates_directory_hostname }} --description "Main DNS server" --protocol udp

curl -o /etc/host.keytab https://{{ penates_directory_fqdn }}/no-auth/get_host_keytab/{{ ansible_nodename }}
k5start -q -f /etc/host.keytab -U -- curl --anyauth -u : https://{{ penates_directory_fqdn }}/auth/set_dhcp/{{ primary_mac_address.stdout }}/?admin_mac_address={{ network_config['admin'][1] }}&admin_ip_address={{ network_config['admin'][2] }}
k5start -q -f /etc/host.keytab -U -- curl --anyauth -u : https://{{ penates_directory_fqdn }}/auth/set_service/ssh/{{ ansible_nodename }}.{{ penates_domain }}/22/?keytab=host
k5start -q -f /etc/host.keytab -U -- curl -o /etc/krb5.keytab --anyauth -u : https://{{ penates_directory_fqdn }}/auth/get_service_keytab/ssh/{{ ansible_nodename }}.{{ penates_domain }}/22/
k5start -q -f /etc/host.keytab -U -- curl -o /etc/ssl/private/host.pem --anyauth -u : https://{{ penates_directory_fqdn }}/auth/get_host_certificate/
k5start -q -f /etc/host.keytab -U -- curl --data-binary @/etc/ssh/ssh_host_ecdsa_key.pub --anyauth -u : https://{{ penates_directory_fqdn }}/auth/set_ssh_pub/
k5start -q -f /etc/host.keytab -U -- curl --anyauth -u : -o /etc/dhcp/dhcpd.conf https://{{ penates_directory_fqdn }}/auth/conf/dhcpd.conf
‚‚‚
"""
from __future__ import unicode_literals
from django.test import TestCase
from penatesserver.powerdns.management.commands.ensure_domain import Command

__author__ = 'Matthieu Gallet'


class TestDns(TestCase):
    domain_name = 'test.example.org'

    def test_complete_scenario(self):
        cmd = Command()
        cmd.handle(domain=self.domain_name)
