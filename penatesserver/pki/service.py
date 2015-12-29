# -*- coding: utf-8 -*-
"""
my_ca = PKI(dirname="/tmp/test")
my_ca.initialize()
my_ca.gen_ca(CertificateEntry("ca.19pouces.net", role=CA))
"""
from __future__ import unicode_literals, with_statement, print_function
import base64
import codecs
import hashlib
import os
import datetime
import re
import shlex
import shutil
from subprocess import CalledProcessError
import subprocess
import tempfile

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.utils.timezone import utc
from penatesserver.filelocks import Lock

from penatesserver.pki.constants import ROLES, RSA, RESOURCE, USER, ENCIPHERMENT, SIGNATURE, EMAIL, COMPUTER_TEST,\
    COMPUTER, CA
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
    def sshfp_sha1(self):
        with codecs.open(self.ssh_filename, 'r', encoding='utf-8') as fd:
            method, content = fd.read().split(' ')
        value = hashlib.sha1(base64.b64decode(content)).hexdigest()
        code = {'ssh-rsa': 1, 'ssh-dss': 2, 'ecdsa-sha2-nistp256': 3, 'ssh-ed25519': 4, }.get(method, 0)
        return '%s 1 %s' % (code, value)

    @property
    def sshfp_sha256(self):
        with codecs.open(self.ssh_filename, 'r', encoding='utf-8') as fd:
            method, content = fd.read().split(' ')
        value = hashlib.sha256(base64.b64decode(content)).hexdigest()
        code = {'ssh-rsa': 1, 'ssh-dss': 2, 'ecdsa-sha2-nistp256': 3, 'ssh-ed25519': 4, }.get(method, 0)
        return '%s 2 %s' % (code, value)

    @property
    def crt_filename(self):
        return os.path.join(self.dirname, 'certs', self.filename + '.crt.pem')

    @property
    def req_filename(self):
        return os.path.join(self.dirname, 'private', 'req', self.filename + '.req.pem')

    @property
    def ca_filename(self):
        return os.path.join(self.dirname, 'cacert.pem')

    @property
    def crt_sha256(self):
        return self.pem_hash(self.crt_filename, hashlib.sha256)

    @property
    def pub_sha256(self):
        return self.pem_hash(self.pub_filename, hashlib.sha256)

    @property
    def crt_sha512(self):
        return self.pem_hash(self.crt_filename, hashlib.sha512)

    @property
    def pub_sha512(self):
        return self.pem_hash(self.pub_filename, hashlib.sha512)

    @staticmethod
    def pem_hash(filename, hash_cls=None):
        if hash_cls is None:
            hash_cls = hashlib.sha256
        with codecs.open(filename, 'r', encoding='utf-8') as fd:
            content = fd.read()
        b64_der = ''.join(content.splitlines()[1:-1])
        der = base64.b64decode(b64_der)
        return hash_cls(der).hexdigest()

    def __repr__(self):
        return self.commonName

    def __unicode__(self):
        return self.commonName

    def __str__(self):
        return self.commonName


class PKI(object):
    def __init__(self, dirname=None):
        self.dirname = dirname or settings.PKI_PATH
        self.cacrl_path = os.path.join(self.dirname, 'cacrl.pem')
        self.careq_path = os.path.join(self.dirname, 'private', 'careq.pem')
        self.crt_sources_path = os.path.join(self.dirname, 'crt_sources.txt')
        self.cacrt_path = os.path.join(self.dirname, 'cacert.pem')
        self.users_crt_path = os.path.join(self.dirname, 'users_crt.pem')
        self.hosts_crt_path = os.path.join(self.dirname, 'hosts_crt.pem')
        self.services_crt_path = os.path.join(self.dirname, 'services_crt.pem')
        self.cakey_path = os.path.join(self.dirname, 'private', 'cakey.pem')
        self.users_key_path = os.path.join(self.dirname, 'private', 'users_key.pem')
        self.hosts_key_path = os.path.join(self.dirname, 'private', 'hosts_key.pem')
        self.services_key_path = os.path.join(self.dirname, 'private', 'services_key.pem')

    def get_subca_infos(self, entry):
        assert isinstance(entry, CertificateEntry)
        if entry.role in (USER, EMAIL, SIGNATURE, ENCIPHERMENT):
            return self.users_crt_path, self.users_key_path
        elif entry.role in (COMPUTER, COMPUTER_TEST):
            return self.hosts_crt_path, self.hosts_key_path
        elif entry.role == CA:
            return self.cacrt_path, self.cakey_path
        return self.services_crt_path, self.services_key_path

    def initialize(self):
        with Lock(settings.PENATES_LOCKFILE):
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
            with Lock(settings.PENATES_LOCKFILE):
                self.__gen_key(entry)
                self.__gen_pub(entry)
                self.__gen_ssh(entry)
        elif not self.__check_pub(entry, entry.pub_filename):
            with Lock(settings.PENATES_LOCKFILE):
                self.__gen_pub(entry)
                self.__gen_ssh(entry)
        elif not self.__check_ssh(entry, entry.ssh_filename):
            with Lock(settings.PENATES_LOCKFILE):
                self.__gen_ssh(entry)

    def ensure_certificate(self, entry):
        """

        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        if not self.__check_key(entry, entry.key_filename):
            with Lock(settings.PENATES_LOCKFILE):
                self.__gen_key(entry)
                self.__gen_pub(entry)
                self.__gen_ssh(entry)
                self.__gen_request(entry)
                self.__gen_certificate(entry)
        elif not self.__check_certificate(entry, entry.crt_filename):
            with Lock(settings.PENATES_LOCKFILE):
                self.__gen_request(entry)
                self.__gen_certificate(entry)

    def __gen_openssl_conf(self, entry=None, ca_infos=None):
        """
        principal: used to define values
        ca: used to define issuer values for settings.CA_POINT, settings.CRL_POINT, settings.OCSP_POINT
        temp_object: used to track temporary files and correctly remove them after use
        keyType: used to define issuer values for settings.CA_POINT, settings.CRL_POINT, settings.OCSP_POINT,
            settings.KERBEROS_REALM
        crts: list of revoked Certificate objects

        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        if ca_infos is None:
            ca_crt_path, ca_key_path = self.cacrt_path, self.cakey_path
        else:
            ca_crt_path, ca_key_path = ca_infos
        context = {'dirname': self.dirname, 'policy_details': [], 'crlPoint': '', 'caPoint': '', 'altSection': '',
                   'altNamesString': '', 'krbRealm': '', 'krbClientName': '', 'ca_key_path': ca_key_path,
                   'ca_crt_path': ca_crt_path, }  # contain all template values
        if entry is not None:
            assert isinstance(entry, CertificateEntry)
            role = ROLES[entry.role]
            for key in ('organizationName', 'organizationalUnitName', 'emailAddress', 'localityName',
                        'stateOrProvinceName', 'countryName', 'commonName'):
                context[key] = getattr(entry, key)
            alt_names = list(entry.altNames)
            for k in ('basicConstraints', 'subjectKeyIdentifier', 'authorityKeyIdentifier',):
                context['policy_details'].append((k, role[k]))
            for k in ('keyUsage', 'extendedKeyUsage', 'nsCertType',):
                context['policy_details'].append((k, ', '.join(role[k])))
            if '1.3.6.1.5.2.3.4' in role['extendedKeyUsage'] and settings.PENATES_REALM:
                alt_names.append(('otherName', '1.3.6.1.5.2.2;SEQUENCE:princ_name'))
                context['krbRealm'] = settings.PENATES_REALM
                context['krbClientName'] = entry.commonName
            if '1.3.6.1.5.2.3.5' in role['extendedKeyUsage'] and settings.PENATES_REALM:
                alt_names.append(('otherName', '1.3.6.1.5.2.2;SEQUENCE:kdc_princ_name'))
                context['krbRealm'] = settings.PENATES_REALM
            if alt_names:
                alt_list = ['{0}.{1} = {2}'.format(alt[0], i, alt[1]) for (i, alt) in enumerate(alt_names)]
                context['altNamesString'] = "\n".join(alt_list)
                context['altSection'] = "subjectAltName=@alt_section"
                if settings.SERVER_NAME:
                    context['crlPoint'] = '%s://%s%s' % (settings.PROTOCOL, settings.SERVER_NAME, reverse('get_crl'))
                    context['caPoint'] = '%s://%s%s' % (settings.PROTOCOL, settings.SERVER_NAME,
                                                        reverse('get_ca_certificate', kwargs={'kind': 'ca'}))
                    # context['ocspPoint'] = config.ocsp_url
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
        # TODO sauvegarde de la clef

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
        subca_infos = self.get_subca_infos(entry)
        conf_path = self.__gen_openssl_conf(entry, ca_infos=subca_infos)
        role = ROLES[entry.role]
        local(('"{openssl}" ca -config "{cfg}" -extensions role_req -in "{req}" -out "{crt}" '
               '-notext -days {days} -md {digest} -batch -utf8 ').format(openssl=settings.OPENSSL_PATH, cfg=conf_path,
                                                                         req=entry.req_filename, crt=entry.crt_filename,
                                                                         days=role['days'], digest=role['digest']))
        serial = self.__get_certificate_serial(entry.crt_filename)
        with codecs.open(self.crt_sources_path, 'a', encoding='utf-8') as fd:
            fd.write('%s\t%s\t%s\t%s\n' % (serial, os.path.relpath(entry.key_filename, self.dirname),
                                           os.path.relpath(entry.req_filename, self.dirname),
                                           os.path.relpath(entry.crt_filename, self.dirname)))

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
        """ si la clef privée de la CA n'existe pas, crée une nouvelle CA
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        """
        if not self.__check_key(entry, self.cakey_path):
            with Lock(settings.PENATES_LOCKFILE):
                self.__gen_ca_key(entry)
                self.__gen_ca_req(entry)
                self.__gen_ca_crt(entry)
            for sub_name in ('users', 'services', 'hosts'):
                sub_entry = CertificateEntry('%s.%s' % (sub_name, entry.commonName),
                                             organizationName=entry.organizationName,
                                             organizationalUnitName=entry.organizationalUnitName,
                                             emailAddress=entry.emailAddress,
                                             localityName=entry.localityName,
                                             countryName=entry.countryName,
                                             stateOrProvinceName=entry.stateOrProvinceName,
                                             dirname=entry.dirname,
                                             role=CA)
                self.ensure_certificate(sub_entry)
                shutil.copy(sub_entry.crt_filename, getattr(self, '%s_crt_path' % sub_name))
                shutil.copy(sub_entry.key_filename, getattr(self, '%s_key_path' % sub_name))

    @staticmethod
    def __check_pub(entry, path):
        """ vrai si la clef publique est valide
        :param entry:
        :type entry: :class:`penatesserver.pki.service.CertificateEntry`
        :return:
        :rtype: `boolean`
        """
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
        # noinspection PyUnusedLocal
        entry = entry
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
        # noinspection PyUnusedLocal
        entry = entry
        if not os.path.isfile(path):
            # logging.warning(_('Request %(path)s of %(cn)s not found') % {'cn': common_name, 'path': path})
            return False
        try:
            local('"{openssl}" req -pubkey -noout -in "{path}"'.format(openssl=settings.OPENSSL_PATH, path=path))
        except CalledProcessError:
            # logging.warning(_('Invalid request %(path)s for %(cn)s') % {'cn': common_name, 'path': path})
            return False
        return True

    def __check_certificate(self, entry, path):
        # noinspection PyUnusedLocal
        entry = entry
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
            # logging.warning(_('Certificate %(path)s for %(cn)s is about to expire') %
            # {'cn': common_name, 'path': path})
            return False
        serial = self.__get_certificate_serial(path)
        if serial is None:
            return False
        elif self.__get_index_file()[serial][1] != 'V':
            return False
        return True

    def revoke_certificate(self, crt_content, regen_crl=True):
        with Lock(settings.PENATES_LOCKFILE):
            with tempfile.NamedTemporaryFile() as fd:
                fd.write(crt_content.encode('utf-8'))
                fd.flush()
                serial = self.__get_certificate_serial(fd.name)
                infos = self.__get_index_file()[serial]
                if infos[1] != 'V':
                    return
                conf_path = self.__gen_openssl_conf()
                local('"{openssl}" ca -config "{cfg}" -revoke {filename}'.format(openssl=settings.OPENSSL_PATH,
                                                                                 cfg=conf_path, filename=fd.name))
        key_filename = os.path.join(self.dirname, infos[5])
        if os.path.isfile(key_filename):
            with open(key_filename, 'rb') as fd:
                content = fd.read()
            os.remove(key_filename)
            with open(key_filename + '.bak', 'ab') as fd:
                fd.write(content)
        req_filename = os.path.join(self.dirname, infos[6])
        if os.path.isfile(req_filename):
            os.remove(req_filename)
        crt_filename = os.path.join(self.dirname, infos[7])
        if os.path.isfile(crt_filename):
            os.remove(crt_filename)
        if regen_crl:
            with Lock(settings.PENATES_LOCKFILE):
                self.__gen_crl(20)

    @staticmethod
    def __get_certificate_serial(filename):
        cmd = [settings.OPENSSL_PATH, 'x509', '-serial', '-noout', '-in', filename]
        serial_text = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8')
        matcher = re.match(r'^serial=([\dA-F]+)$', serial_text.strip())
        if not matcher:
            return None
        return matcher.group(1)

    def ensure_crl(self):
        if not self.__check_crl():
            with Lock(settings.PENATES_LOCKFILE):
                self.__gen_crl(20)

    def __check_crl(self):
        try:
            content = subprocess.check_output([settings.OPENSSL_PATH, 'crl', '-noout', '-nextupdate', '-in',
                                               self.cacrl_path], stderr=subprocess.PIPE)
        except CalledProcessError:
            return False
        key, sep, value = content.decode('utf-8').partition('=')
        if key != 'nextUpdate' or sep != '=':
            return False
        return t61_to_time(value.strip()) > (datetime.datetime.now(utc) + datetime.timedelta(seconds=86400))

    def __gen_crl(self, crldays):
        config = self.__gen_openssl_conf()
        content = subprocess.check_output([settings.OPENSSL_PATH, 'ca', '-gencrl', '-utf8', '-config', config,
                                           '-keyfile', self.cakey_path, '-cert', self.cacrt_path, '-crldays',
                                           str(crldays)], stderr=subprocess.PIPE)
        with open(self.cacrl_path, 'wb') as fd:
            fd.write(content)

    def __get_index_file(self):
        """Return a dict ["serial"] = ["serial", "V|R", "valid_date", "revoke_date", "cn", "key filename",
        "req filename", "crt filename"]
        :return:
        :rtype:
        """
        result = {}
        with codecs.open(os.path.join(self.dirname, 'index.txt'), 'r', encoding='utf-8') as fd:
            for line in fd:
                if not line:
                    continue
                state, valid_date, revoke_date, serial, unused, cn = line.split('\t')
                result[serial] = [serial, state, valid_date, revoke_date, cn, None, None, None]
        if os.path.isfile(self.crt_sources_path):
            with codecs.open(self.crt_sources_path, 'r', encoding='utf-8') as fd:
                for line in fd:
                    if not line:
                        continue
                    serial, key, req, crt = line.split('\t')
                    result[serial][5] = key
                    result[serial][6] = req
                    result[serial][7] = crt
        return result

    def gen_pkcs12(self, entry, filename, password):
        assert isinstance(entry, CertificateEntry)
        self.ensure_certificate(entry)
        with tempfile.NamedTemporaryFile() as fd:
            fd.write(password.encode('utf-8'))
            fd.flush()
            p = subprocess.Popen([settings.OPENSSL_PATH, 'pkcs12', '-export', '-out', filename, '-passout',
                                  'file:%s' % fd.name, '-aes256', '-in', entry.crt_filename, '-inkey',
                                  entry.key_filename, '-certfile', self.cacrt_path, '-name', entry.filename, ])
            p.communicate()
