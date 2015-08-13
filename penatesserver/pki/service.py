# -*- coding: utf-8 -*-
"""
my_ca = PKI(dirname="/tmp/test")
my_ca.initialize()
my_ca.gen_ca(CertificateEntry("ca.19pouces.net", role=CA))
"""
from __future__ import unicode_literals, with_statement, print_function
import codecs
import os
import datetime
import shlex
from subprocess import CalledProcessError
import subprocess
import tempfile

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.utils.timezone import utc

from penatesserver.pki.constants import ROLES, RSA, RESOURCE
from penatesserver.utils import t61_to_time, ensure_location


def local(command, cwd=None):
    return subprocess.check_output(shlex.split(command), shell=False, cwd=cwd, stderr=subprocess.PIPE)


__author__ = 'Matthieu Gallet'


class CertificateEntry(object):
    # noinspection PyPep8Naming
    def __init__(self, commonName, organizationName='', organizationalUnitName='', emailAddress='', localityName='',
                 countryName='', stateOrProvinceName='', altNames=None, role=RESOURCE, dirname=None):
        # altNames must be a list of couples (ALT_EMAIL|ALT_DNS|ALT_URI, value)
        self.commonName = commonName
        self.organizationName = organizationName
        self.organizationalUnitName = organizationalUnitName
        self.emailAddress = emailAddress
        self.localityName = localityName
        self.countryName = countryName
        self.stateOrProvinceName = stateOrProvinceName
        self.altNames = altNames or []
        self.role = role
        self.dirname = dirname or settings.PKI_PATH

    @property
    def filename(self):
        basename = '%s_%s' % (self.role, self.commonName)
        return slugify(basename)

    @property
    def values(self):
        return ROLES[self.role]

    @property
    def key_filename(self):
        return os.path.join(self.dirname, 'private', 'keys', self.filename + '.key.pem')

    @property
    def pub_filename(self):
        return os.path.join(self.dirname, 'pubkeys', self.filename + '.pub.pem')

    @property
    def ssh_filename(self):
        return os.path.join(self.dirname, 'pubsshkeys', self.filename + '.pub')

    @property
    def crt_filename(self):
        return os.path.join(self.dirname, 'certs', self.filename + '.crt.pem')

    @property
    def req_filename(self):
        return os.path.join(self.dirname, 'private', 'req', self.filename + '.req.pem')

    @property
    def ca_filename(self):
        return os.path.join(self.dirname, 'cacert.pem')

    def __repr__(self):
        return self.commonName

    def __unicode__(self):
        return self.commonName

    def __str__(self):
        return self.commonName


class PKI(object):
    def __init__(self, dirname=None):
        self.dirname = dirname or settings.PKI_PATH
        self.cacrt_path = os.path.join(self.dirname, 'cacert.pem')
        self.cakey_path = os.path.join(self.dirname, 'private', 'cakey.pem')

    def initialize(self):
        serial = os.path.join(self.dirname, 'serial.txt')
        index = os.path.join(self.dirname, 'index.txt')
        ensure_location(serial)
        if not os.path.isfile(serial):
            with codecs.open(serial, 'w', encoding='utf-8') as fd:
                fd.write("01\n")
        if not os.path.isfile(index):
            with codecs.open(index, 'w', encoding='utf-8') as fd:
                fd.write("")
        ensure_location(os.path.join(self.dirname, 'new_certs', '0'))

    def ensure_key(self, entry):
        """
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        if not self.__check_key(entry, entry.key_filename):
            self.__gen_key(entry)
            self.__gen_pub(entry)
            self.__gen_ssh(entry)
        elif not self.__check_pub(entry, entry.pub_filename):
            self.__gen_pub(entry)
            self.__gen_ssh(entry)
        elif not self.__check_ssh(entry, entry.ssh_filename):
            self.__gen_ssh(entry)

    def ensure_certificate(self, entry):
        """

        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        if not self.__check_key(entry, entry.key_filename):
            self.__gen_key(entry)
            self.__gen_pub(entry)
            self.__gen_request(entry)
            self.__gen_certificate(entry)
        elif not self.__check_req(entry, entry.req_filename):
            self.__gen_request(entry)
            self.__gen_certificate(entry)
        elif not self.__check_certificate(entry, entry.crt_filename):
            self.__gen_certificate(entry)

    def __gen_openssl_conf(self, entry=None):
        """
        principal: used to define values
        ca: used to define issuer values for settings.CA_POINT, settings.CRL_POINT, settings.OCSP_POINT
        temp_object: used to track temporary files and correctly remove them after use
        keyType: used to define issuer values for settings.CA_POINT, settings.CRL_POINT, settings.OCSP_POINT,
            settings.KERBEROS_REALM
        crts: list of revoked Certificate objects

        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        context = {'dirname': self.dirname, 'policy_details': [],
                   'crlPoint': '', 'caPoint': '', 'altSection': '', 'altNamesString': '',
                   'krbRealm': '', 'krbClientName': '', }  # contain all template values
        if entry is not None:
            role = ROLES[entry.role]
            for key in ('organizationName', 'organizationalUnitName', 'emailAddress', 'localityName',
                        'stateOrProvinceName', 'countryName', 'commonName'):
                context[key] = getattr(entry, key)
            alt_names = list(entry.altNames)
            for k in ('basicConstraints', 'subjectKeyIdentifier', 'authorityKeyIdentifier', ):
                context['policy_details'].append((k, role[k]))
            for k in ('keyUsage', 'extendedKeyUsage', 'nsCertType', ):
                context['policy_details'].append((k, ', '.join(role[k])))
            if '1.3.6.1.5.2.3.4' in role['extendedKeyUsage'] and settings.SAMBA4_REALM:
                alt_names.append(('otherName', '1.3.6.1.5.2.2;SEQUENCE:princ_name'))
                context['krbRealm'] = settings.SAMBA4_REALM
                context['krbClientName'] = entry.commonName
            if '1.3.6.1.5.2.3.5' in role['extendedKeyUsage'] and settings.SAMBA4_REALM:
                alt_names.append(('otherName', '1.3.6.1.5.2.2;SEQUENCE:kdc_princ_name'))
                context['krbRealm'] = settings.SAMBA4_REALM
            if alt_names:
                alt_list = ['{0}.{1} = {2}'.format(alt[0], i, alt[1]) for (i, alt) in enumerate(alt_names)]
                context['altNamesString'] = "\n".join(alt_list)
                context['altSection'] = "subjectAltName=@alt_section"
            # context['crlPoint'] = config.crl_url
            # context['ocspPoint'] = config.ocsp_url
            # context['caPoint'] = config.ca_url
            # build a file structure which is compatible with ``openssl ca'' commands
        # noinspection PyUnresolvedReferences
        conf_content = render_to_string('penatesserver/pki/openssl.cnf', context)
        conf_path = os.path.join(self.dirname, 'openssl.cnf')
        with codecs.open(conf_path, 'w', encoding='utf-8') as conf_fd:
            conf_fd.write(conf_content)
        return conf_path

    @staticmethod
    def __gen_key(entry):
        """ génère la clef privée pour l'entrée fournie
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        role = ROLES[entry.role]
        ensure_location(entry.key_filename)
        if role['keyType'] == RSA:
            local('"{openssl}" genrsa -out {key} {bits}'.format(bits=role['rsaBits'], openssl=settings.OPENSSL_PATH,
                                                                key=entry.key_filename))
        else:
            with tempfile.NamedTemporaryFile() as fd:
                param = fd.name
            local('"{openssl}" dsaparam -rand -genkey {bits} -out "{param}"'.format(bits=role['dsaBits'],
                                                                                    openssl=settings.OPENSSL_PATH,
                                                                                    param=param))
            local('"{openssl}" gendsa -out "{key}" "{param}"'.format(openssl=settings.OPENSSL_PATH, param=param,
                                                                     key=entry.key_filename))
            os.remove(param)
        os.chmod(entry.key_filename, 0o600)

    @staticmethod
    def __gen_pub(entry):
        """ génère la clef publique pour l'entrée fournie
        la clef privée doit exister
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        role = ROLES[entry.role]
        ensure_location(entry.pub_filename)
        if role['keyType'] == RSA:
            local('"{openssl}" rsa -in "{key}" -out "{pub}" -pubout'.format(openssl=settings.OPENSSL_PATH,
                                                                            key=entry.key_filename,
                                                                            pub=entry.pub_filename))
        else:
            local('"{openssl}" dsa -in "{key}" -out "{pub}" -pubout'.format(openssl=settings.OPENSSL_PATH,
                                                                            key=entry.key_filename,
                                                                            pub=entry.pub_filename))

    @staticmethod
    def __gen_ssh(entry):
        """ génère la clef publique SSH pour l'entrée fournie
        la clef privée doit exister
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        result = local('"{ssh_keygen}" -y -f "{inkey}" '.format(inkey=entry.key_filename,
                                                                ssh_keygen=settings.SSH_KEYGEN_PATH))
        ensure_location(entry.ssh_filename)
        with open(entry.ssh_filename, 'wb') as ssh_fd:
            ssh_fd.write(result)

    def __gen_request(self, entry):
        """ génère une demande de certificat pour l'entrée fournie
        la clef privée doit exister
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        conf_path = self.__gen_openssl_conf(entry)
        role = ROLES[entry.role]
        ensure_location(entry.req_filename)
        local(('"{openssl}" req  -out "{out}" -batch -utf8 -new -key "{inkey}" -{digest} -config "{config}" '
               '-extensions role_req').format(openssl=settings.OPENSSL_PATH, inkey=entry.key_filename,
                                              digest=role['digest'], config=conf_path, out=entry.req_filename))

    def __gen_certificate(self, entry):
        """ génère un certificat pour l'entrée fournie
        la demande de certificat doit exister, ainsi que la CA
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        ensure_location(entry.crt_filename)
        conf_path = self.__gen_openssl_conf(entry)
        role = ROLES[entry.role]
        local(('"{openssl}" ca -config "{cfg}" -extensions role_req -in "{req}" -out "{crt}" '
               '-notext -days {days} -md {digest} -batch -utf8 ').format(openssl=settings.OPENSSL_PATH, cfg=conf_path,
                                                                         req=entry.req_filename, crt=entry.crt_filename,
                                                                         days=role['days'], digest=role['digest']))

    def __gen_ca_key(self, entry):
        """
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        role = ROLES[entry.role]
        ensure_location(self.cakey_path)
        if role['keyType'] == RSA:
            local('"{openssl}" genrsa -out {key} {bits}'.format(bits=role['rsaBits'], openssl=settings.OPENSSL_PATH,
                                                                key=self.cakey_path))
        else:
            with tempfile.NamedTemporaryFile() as fd:
                param = fd.name
            local('"{openssl}" dsaparam -rand -genkey {bits} -out "{param}"'.format(bits=role['dsaBits'],
                                                                                    openssl=settings.OPENSSL_PATH,
                                                                                    param=param))
            local('"{openssl}" gendsa -out "{key}" "{param}"'.format(openssl=settings.OPENSSL_PATH, param=param,
                                                                     key=self.cakey_path))
            os.remove(param)
        os.chmod(self.cakey_path, 0o600)

    def __gen_ca_req(self, entry):
        """
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        role = ROLES[entry.role]
        ensure_location(entry.req_filename)
        conf_path = self.__gen_openssl_conf(entry)
        local(('"{openssl}" req  -out "{out}" -batch -utf8 -new -key "{inkey}" -{digest} -config "{config}" '
               '-extensions role_req').format(openssl=settings.OPENSSL_PATH, inkey=self.cakey_path,
                                              digest=role['digest'], config=conf_path, out=entry.req_filename))

    def __gen_ca_crt(self, entry):
        """
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        conf_path = self.__gen_openssl_conf(entry)
        role = ROLES[entry.role]
        ensure_location(self.cacrt_path)
        local(('"{openssl}" ca -config "{cfg}" -selfsign -extensions role_req -in "{req}" -out "{crt}" '
               '-notext -days {days} -md {digest} -batch -utf8 ').format(openssl=settings.OPENSSL_PATH, cfg=conf_path,
                                                                         req=entry.req_filename, crt=self.cacrt_path,
                                                                         days=role['days'], digest=role['digest']))

    def ensure_ca(self, entry):
        """ génère un certificat pour l'entrée fournie
        la demande de certificat doit exister, ainsi que la CA
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        if not self.__check_key(entry, self.cakey_path):
            self.__gen_ca_key(entry)
            self.__gen_ca_req(entry)
            self.__gen_ca_crt(entry)
        elif not self.__check_req(entry, entry.req_filename):
            self.__gen_ca_req(entry)
            self.__gen_ca_crt(entry)
        elif not self.__check_certificate(entry, self.cacrt_path):
            self.__gen_ca_crt(entry)

    @staticmethod
    def __check_pub(entry, path):
        """ vrai si la clef publique est valide
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        :return:
        :rtype: `boolean`
        """
        common_name = entry.commonName
        if not os.path.isfile(path):
            # logging.warning(_('Public key %(path)s of %(cn)s not found') % {'cn': common_name, 'path': path})
            return False
        cmd = 'rsa' if ROLES[entry.role]['keyType'] == RSA else 'dsa'
        try:
            local('"{openssl}" {cmd} -pubout -pubin -in "{path}"'.format(openssl=settings.OPENSSL_PATH, cmd=cmd,
                                                                         path=path))
        except CalledProcessError:
            # logging.warning(_('Invalid public key %(path)s for %(cn)s') % {'cn': common_name, 'path': path})
            return False
        return True

    @staticmethod
    def __check_key(entry, path):
        """ vrai si la clef privée est valide
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        :return:
        :rtype: `boolean`
        """
        common_name = entry.commonName
        if not os.path.isfile(path):
            # logging.warning(_('Private key %(path)s of %(cn)s not found') % {'cn': common_name, 'path': path})
            return False
        cmd = 'rsa' if ROLES[entry.role]['keyType'] == RSA else 'dsa'
        try:
            local('"{openssl}" {cmd} -pubout -in "{path}"'.format(openssl=settings.OPENSSL_PATH, cmd=cmd, path=path))
        except CalledProcessError:
            # logging.warning(_('Invalid private key %(path)s for %(cn)s') % {'cn': common_name, 'path': path})
            return False
        return True

    @staticmethod
    def __check_ssh(entry, path):
        """ vrai si la clef publique SSH est valide
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        :return:
        :rtype: `boolean`
        """
        common_name = entry.commonName
        if not os.path.isfile(path):
            # logging.warning(_('SSH public key %(path)s of %(cn)s not found') % {'cn': common_name, 'path': path})
            return False
        return True

    @staticmethod
    def __check_req(entry, path):
        """ vrai si la requête est valide
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        :return:
        :rtype: `boolean`
        """
        common_name = entry.commonName
        if not os.path.isfile(path):
            # logging.warning(_('Request %(path)s of %(cn)s not found') % {'cn': common_name, 'path': path})
            return False
        try:
            local('"{openssl}" req -pubkey -noout -in "{path}"'.format(openssl=settings.OPENSSL_PATH, path=path))
        except CalledProcessError:
            # logging.warning(_('Invalid request %(path)s for %(cn)s') % {'cn': common_name, 'path': path})
            return False
        return True

    @staticmethod
    def __check_certificate(entry, path):
        common_name = entry.commonName
        if not os.path.isfile(path):
            # logging.warning(_('Certificate %(path)s of %(cn)s not found') % {'cn': common_name, 'path': path})
            return False
        try:
            stdout = local('"{openssl}" x509 -enddate -noout -in "{path}"'.format(openssl=settings.OPENSSL_PATH,
                                                                                  path=path))
        except CalledProcessError:
            # logging.warning(_('Invalid certificate %(path)s for %(cn)s') % {'cn': common_name, 'path': path})
            return False
        stdout = stdout.decode('utf-8')
        end_date = t61_to_time(stdout.partition('=')[2].strip())
        after_now = datetime.datetime.now(tz=utc) + datetime.timedelta(30)
        if end_date is None or end_date < after_now:
            # logging.warning(_('Certificate %(path)s for %(cn)s is about to expire') % {'cn': common_name, 'path': path})
            return False
        return True
