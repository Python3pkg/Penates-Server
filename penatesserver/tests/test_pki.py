# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import os
import tempfile
import shutil
from django.conf import settings

from django.test import TestCase
import subprocess

from penatesserver.pki.constants import CA_TEST, COMPUTER_TEST, TEST_DSA, TEST_SHA256
from penatesserver.pki.service import CertificateEntry, PKI

__author__ = 'Matthieu Gallet'


class TestCA(TestCase):
    @classmethod
    def setUpClass(cls):
        TestCase.setUpClass()
        cls.dirname = tempfile.mkdtemp()
        cls.pki = PKI(dirname=cls.dirname)
        cls.ca_entry = CertificateEntry('test_CA', organizationName='test_org', organizationalUnitName='test_unit',
                                        emailAddress='test@example.com', localityName='City',
                                        countryName='FR', stateOrProvinceName='Province', altNames=[],
                                        role=CA_TEST, dirname=cls.dirname)

    @classmethod
    def tearDownClass(cls):
        # noinspection PyUnresolvedReferences
        shutil.rmtree(cls.dirname)

    def test_ca(self):
        self.pki.initialize()
        self.pki.ensure_ca(self.ca_entry)
        self.assertTrue(os.path.isfile(self.pki.cacrt_path))
        self.assertTrue(os.path.isfile(self.pki.cakey_path))


class TestPKI(TestCase):
    @classmethod
    def setUpClass(cls):
        TestCase.setUpClass()
        cls.dirname = tempfile.mkdtemp()
        cls.pki = PKI(dirname=cls.dirname)
        cls.ca_entry = CertificateEntry('test_CA', organizationName='test_org', organizationalUnitName='test_unit',
                                        emailAddress='test@example.com', localityName='City',
                                        countryName='FR', stateOrProvinceName='Province', altNames=[],
                                        role=CA_TEST, dirname=cls.dirname)
        cls.pki.initialize()
        cls.pki.ensure_ca(cls.ca_entry)
        cls.tmp_filenames = []

    @classmethod
    def tearDownClass(cls):
        # noinspection PyUnresolvedReferences
        shutil.rmtree(cls.dirname)
        # noinspection PyUnresolvedReferences
        for filename in cls.tmp_filenames:
            if os.path.isfile(filename):
                os.remove(filename)

    @classmethod
    def get_tmp_filename(cls):
        with tempfile.NamedTemporaryFile() as fd:
            filename = fd.name
        # noinspection PyUnresolvedReferences
        cls.tmp_filenames.append(filename)
        return filename


class TestCertRole(TestPKI):
    def test_ca(self):
        self.assertTrue(os.path.isfile(self.pki.cacrt_path))
        self.assertTrue(os.path.isfile(self.pki.cakey_path))

    def test_computer(self):
        entry = CertificateEntry('test_computer', organizationName='test_org', organizationalUnitName='test_unit',
                                 emailAddress='test@example .com', localityName='City',
                                 countryName='FR', stateOrProvinceName='Province', altNames=[],
                                 role=COMPUTER_TEST, dirname=self.dirname)
        self.pki.ensure_certificate(entry)
        self.assertTrue(entry.pub_filename)
        self.assertTrue(entry.key_filename)
        self.assertTrue(entry.crt_filename)
        self.assertTrue(entry.ssh_filename)

    def test_computer_dsa(self):
        entry = CertificateEntry('test_dsa', organizationName='test_org', organizationalUnitName='test_unit',
                                 emailAddress='test@example .com', localityName='City',
                                 countryName='FR', stateOrProvinceName='Province', altNames=[],
                                 role=TEST_DSA, dirname=self.dirname)
        self.pki.ensure_certificate(entry)
        self.assertTrue(entry.pub_filename)
        self.assertTrue(entry.key_filename)
        self.assertTrue(entry.crt_filename)
        self.assertTrue(entry.ssh_filename)

    def test_computer_sha256(self):
        entry = CertificateEntry('test_sha256', organizationName='test_org', organizationalUnitName='test_unit',
                                 emailAddress='test@example .com', localityName='City',
                                 countryName='FR', stateOrProvinceName='Province', altNames=[],
                                 role=TEST_SHA256, dirname=self.dirname)
        self.pki.ensure_certificate(entry)
        self.assertTrue(entry.pub_filename)
        self.assertTrue(entry.key_filename)
        self.assertTrue(entry.crt_filename)
        self.assertTrue(entry.ssh_filename)

    def test_export_pkcs12(self):
        entry = CertificateEntry('test_pkcs12', organizationName='test_org', organizationalUnitName='test_unit',
                                 emailAddress='test@example .com', localityName='City',
                                 countryName='FR', stateOrProvinceName='Province', altNames=[],
                                 role=TEST_SHA256, dirname=self.dirname)
        filename = self.get_tmp_filename()
        password = 'password'
        self.pki.gen_pkcs12(entry, filename=filename, password=password)
        with codecs.open(entry.key_filename, 'r', encoding='utf-8') as fd:
            src_key_content = fd.read()
        password_file = self.get_tmp_filename()
        with codecs.open(password_file, 'w', encoding='utf-8') as fd:
            fd.write(password)
            fd.flush()
        p = subprocess.Popen([settings.OPENSSL_PATH, 'pkcs12', '-in', filename, '-passin', 'file:%s' % password_file,
                              '-nodes', '-nocerts', ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate(input=password.encode('utf-8'))
        dst_key_content = stdout.decode('utf-8')
        self.assertTrue(src_key_content in dst_key_content)


class TestCrl(TestPKI):
    def test_crl(self):
        entry = CertificateEntry('test_computer', organizationName='test_org', organizationalUnitName='test_unit',
                                 emailAddress='test@example .com', localityName='City',
                                 countryName='FR', stateOrProvinceName='Province', altNames=[],
                                 role=COMPUTER_TEST, dirname=self.dirname)
        self.pki.ensure_certificate(entry)
        with codecs.open(entry.crt_filename, 'r', encoding='utf-8') as fd:
            content = fd.read()
        self.pki.ensure_crl()
        self.pki.ensure_crl()
        self.pki.revoke_certificate(content)
        self.pki.ensure_certificate(entry)
        self.pki.ensure_certificate(entry)
        with open(self.pki.dirname + '/index.txt', b'r') as fd:
            self.assertEqual(6, len(fd.read().splitlines()))


class TestSha256(TestCase):
    def test_sha256(self):
        with tempfile.NamedTemporaryFile() as fd:
            fd.write("""-----BEGIN CERTIFICATE-----
MIIG8TCCBNmgAwIBAgIBBjANBgkqhkiG9w0BAQsFADCBjjEZMBcGA1UEAxMQdGVz
dC5leGFtcGxlLm9yZzElMCMGCSqGSIb3DQEJARYWYWRtaW5AdGVzdC5leGFtcGxl
Lm9yZzEVMBMGA1UECxMMQ2VydGlmaWNhdGVzMQ4wDAYDVQQHEwVQYXJpczEWMBQG
A1UECBMNSWxlLWRlLUZyYW5jZTELMAkGA1UEBhMCRlIwHhcNMTUwOTE3MjA1NDM3
WhcNMTgwNjEzMjA1NDM3WjCBozEgMB4GA1UEAxMXbWFpbDAxLnRlc3QuZXhhbXBs
ZS5vcmcxJTAjBgkqhkiG9w0BCQEWFmFkbWluQHRlc3QuZXhhbXBsZS5vcmcxEDAO
BgNVBAoTB0VYQU1QTEUxETAPBgNVBAsTCFNlcnZpY2VzMQ4wDAYDVQQHEwVQYXJp
czEWMBQGA1UECBMNSWxlLWRlLUZyYW5jZTELMAkGA1UEBhMCRlIwggIiMA0GCSqG
SIb3DQEBAQUAA4ICDwAwggIKAoICAQDE64r5Y/1UEDGOY+T0wLs00mDUTzfSKaCb
mAgHm9cgTSNYg1H6dAYAitLPnOS2ish/rp8VjZrHU3F4VR7gswtOp5p3c8GNxRB6
gS/hNcoByuVwd9E5yXaE9L+OerdDjRJhKiws9/d6V0Zur8LaBLUjVY1XOvW5/GuO
qlqT02mA2W0i+NmETZjsYJOjt280ZgXgkZ+26V1I5AD9O7D70yUPvnja69quy7z6
HFMcPfrJnX+j14vj25GsyOp0xUp0YkUhZag0/8HbxNTDu10b30JMQfjZ6VuceQRQ
KoFgx/IrSIhRO9EHey/3DK7AUE++bOXJuIgxQCgTtcd6nTjMO107a128nnoB6XO+
1PhZ6MiLnUhxk7Pc9+TLOI0X/3X9o03D29vNW4GT/iGeoVkMkzy3q3m7DfHdJ/GC
9hZ3RtfnLWG/StuXXejgqgy6opIeXTChk85CDm0EuOMwm1bApqIw4gD4FH8RDRLC
HLSq22kKmC76yvRH39+wNK2u2HO+2whMxgcjiV650xvBcMrqFrWJzMXVF4h68r7J
oc/LNUuZlYQZp2l6+zWpxVOIx57PYTfgyZtwF7bnpsGBAqm0GIDDWdutJ7XuMxV0
j3RfxR80uvuoODYrmy0Hx6/a1P5vJVMSiqR0CXIwA6l7N9DiUDhmouuT9hrQ9xYz
bbTAqageaQIDAQABo4IBQTCCAT0wCQYDVR0SBAIwADAJBgNVHRMEAjAAMB0GA1Ud
DgQWBBTPqjgVEEGTw8vCpZWi2r7BQ6qo6TCBuwYDVR0jBIGzMIGwgBS7We5+rpWD
t4gY7+SIckpoIYz2jKGBlKSBkTCBjjEZMBcGA1UEAxMQdGVzdC5leGFtcGxlLm9y
ZzElMCMGCSqGSIb3DQEJARYWYWRtaW5AdGVzdC5leGFtcGxlLm9yZzEVMBMGA1UE
CxMMQ2VydGlmaWNhdGVzMQ4wDAYDVQQHEwVQYXJpczEWMBQGA1UECBMNSWxlLWRl
LUZyYW5jZTELMAkGA1UEBhMCRlKCAQEwCwYDVR0PBAQDAgO4MCgGA1UdJQQhMB8G
CCsGAQUFBwMCBglghkgBhvhCBAEGCCsGAQUFBwMBMBEGCWCGSAGG+EIBAQQEAwIG
wDANBgkqhkiG9w0BAQsFAAOCAgEAN9CrPyxDf39Rc4vgJ/0h2HT6jSvV2YvPObaH
L1m/pfPlAdTc/n6NwmQ/OwF0bt/xxpoMgRFI+GpbCr46S/QC1lAzfdQdnqj94Twx
f5547sSTmNMZakYeWSFXw5cH2uUQW0v0Rt/TaXlzOKTxquXeDpShHnj4s+E03ani
AWCKVbchCeUR/CP4Z+yzNbKQcJurPOKaZSeTN7IvRujIKr54VkhRJ4C8E4FrHbPg
vHGNqMMXUhdCXow7GgQVOPkrR47x2ZfjgITgiIneX6aMyEcsEm9R1CCA9O4KYJ5R
wnVPjQR1DP3947kkutRv3a/s0rbFSwLpO263F4zeu5X87g/d/QFT6u0NrqdlDqUd
0Fg0wKrqmVPuTbM5/siaw+CYXpDJMl7fgGmjhatcD+tuNgxtPX3Ax9bOHuznDlLQ
Ok5swYjjA3JJlML+Y9QFLiq1YZqNjRuZgh4VzCcAcXIITXKLY6ffTxAAydDXCSUO
OTEoBFbz19jkUG6psC9TwqZ8Ol8T2fFKh0E2bZEZZOEMkce9VEfoje+jD+Xcxs+2
8igeG9UXBr4j8Q6FXO958DSnQIQNKRce5T46VugwIiyZrMRySzoWMO1cbmV6kwZG
i57f4l17ztci4pTZLSwIiiCDN20zCtmMagoVRrXZRhaQhrSLag1GvMezFIABEV/O
QPlWtMI=
-----END CERTIFICATE-----""".encode('utf-8'))
            fd.flush()
            sha256 = CertificateEntry.pem_hash(fd.name)
            self.assertEqual("9a057dc87450e2b4c20c4c567dfcb952f890ad22fd20e0ddfb588d5c6680840f", sha256)

    def test_pubkey_sha256(self):
        with tempfile.NamedTemporaryFile() as fd:
            fd.write("""-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAxOuK+WP9VBAxjmPk9MC7
NNJg1E830imgm5gIB5vXIE0jWINR+nQGAIrSz5zktorIf66fFY2ax1NxeFUe4LML
Tqead3PBjcUQeoEv4TXKAcrlcHfROcl2hPS/jnq3Q40SYSosLPf3eldGbq/C2gS1
I1WNVzr1ufxrjqpak9NpgNltIvjZhE2Y7GCTo7dvNGYF4JGftuldSOQA/Tuw+9Ml
D7542uvarsu8+hxTHD36yZ1/o9eL49uRrMjqdMVKdGJFIWWoNP/B28TUw7tdG99C
TEH42elbnHkEUCqBYMfyK0iIUTvRB3sv9wyuwFBPvmzlybiIMUAoE7XHep04zDtd
O2tdvJ56AelzvtT4WejIi51IcZOz3PfkyziNF/91/aNNw9vbzVuBk/4hnqFZDJM8
t6t5uw3x3SfxgvYWd0bX5y1hv0rbl13o4KoMuqKSHl0woZPOQg5tBLjjMJtWwKai
MOIA+BR/EQ0Swhy0qttpCpgu+sr0R9/fsDStrthzvtsITMYHI4leudMbwXDK6ha1
iczF1ReIevK+yaHPyzVLmZWEGadpevs1qcVTiMeez2E34MmbcBe256bBgQKptBiA
w1nbrSe17jMVdI90X8UfNLr7qDg2K5stB8ev2tT+byVTEoqkdAlyMAOpezfQ4lA4
ZqLrk/Ya0PcWM220wKmoHmkCAwEAAQ==
-----END PUBLIC KEY-----""".encode('utf-8'))
            fd.flush()
            sha256 = CertificateEntry.pem_hash(fd.name)
            self.assertEqual("bf2f7adbc2bd0865bf65d41b9a7277b531fb3618c00ea339256e9e76ffbdb4e6", sha256)

