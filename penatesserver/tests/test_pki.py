# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import tempfile
import shutil
from django.test import TestCase

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

    @classmethod
    def tearDownClass(cls):
        # noinspection PyUnresolvedReferences
        shutil.rmtree(cls.dirname)

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
