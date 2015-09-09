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
            self.assertEqual(3, len(fd.read().splitlines()))
