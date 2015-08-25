# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from base64 import b64encode, b64decode
from collections import OrderedDict
import datetime
import hashlib
import os
import random
import re
import string
from django.http import HttpResponse
from django.utils.timezone import utc
from penatesserver.pki.service import PKI

T61_RE = re.compile(r'^([A-Z][a-z]{2}) {1,2}(\d{1,2}) (\d{1,2}):(\d{1,2}):(\d{1,2}) (\d{4}).*$')


def force_bytestrings(unicode_list):
    """
     >>> force_bytestrings(['test']) == [b'test']
     True
    """
    return [x.encode('utf-8') for x in unicode_list]


def force_bytestring(x):
    return x.encode('utf-8')


def t61_to_time(d):
    """
    >>> t61_to_time('Jul  8 14:01:58 2037 GMT') is not None
    True
    >>> t61_to_time('Jul  8 14:01:58 2037 GMT').year
    2037

    :param d:
    :type d:
    :return:
    :rtype:
    """
    matcher = T61_RE.match(d)
    if matcher:
        groups = matcher.groups()
        month = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9,
                 'Oct': 10, 'Nov': 11, 'Dec': 12}[groups[0]]
        return datetime.datetime(int(groups[5][-2:]) + 2000, month, int(groups[1]), int(groups[2]), int(groups[3]),
                                 int(groups[4]), tzinfo=utc)
    return None


def ensure_location(filename):
    dirname = os.path.dirname(filename)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)


def hostname_from_principal(principal):
    """
    >>> hostname_from_principal('HOST/test.example.org') == 'test.example.org'
    True
    >>> hostname_from_principal('HOST/test.example.org@TEST.EXAMPLE.ORG') == 'test.example.org'
    True
    """
    if not principal.startswith('HOST/'):
        raise ValueError
    return principal[5:].partition('@')[0]


def principal_from_hostname(hostname, realm):
    """
    >>> principal_from_hostname('test.example.org', 'TEST.EXAMPLE.ORG') == 'HOST/test.example.org@TEST.EXAMPLE.ORG'
    True
    """
    return 'HOST/%s@%s' % (hostname, realm)


def ensure_list(value):
    """
    >>> ensure_list(1)
    [1]
    >>> ensure_list([1, 2])
    [1, 2]
    >>> ensure_list((1, 2))
    [1, 2]
    >>> ensure_list({1, 2})
    [1, 2]

    """
    if isinstance(value, list):
        return value
    elif isinstance(value, set) or isinstance(value, tuple):
        return [x for x in value]
    return [value]


def dhcp_list_to_dict(value_list):
    """Convert a list of DHCP values to a dict
    >>> dhcp_list_to_dict(['key1 value11 value12', 'key2 value21 value22 value23']) == OrderedDict([('key1', ['value11', 'value12']), ('key2', ['value21', 'value22', 'value23'])])
    True

    :rtype: :class:`collections.OrderedDict`
    """
    result = OrderedDict()
    for value in value_list:
        splitted_values = value.split()
        if len(splitted_values) > 1:
            result[splitted_values[0]] = splitted_values[1:]
    return result


def dhcp_dict_to_list(value_dict):
    """ Convert a dict to a list of DHCP values

    >>> dhcp_dict_to_list(dhcp_list_to_dict(['key1 value11 value12', 'key2 value21 value22 value23'])) == ['key1 value11 value12', 'key2 value21 value22 value23']
    True

    >>> dhcp_dict_to_list(dhcp_list_to_dict(['key1 value11 value12', 'key2 value21 value22 value23'])) == ['key1 value11 value12', 'key2 value21 value22 value23']
    True

    :rtype: :class:`list`
    """
    return ['%s %s' % (key, ' '.join(ensure_list(value))) for (key, value) in value_dict.items()]


def guess_use_ssl(scheme):
    use_ssl = False
    if scheme.endswith('s') and scheme != 'dns':
        scheme, use_ssl = scheme[:-1], True
    return scheme, use_ssl


def get_salt(chars=string.ascii_letters + string.digits, length=16):
    """Generate a random salt. Default length is 16.
       Originated from mkpasswd in Luma
    """
    salt = ""
    for i in range(int(length)):
        salt += random.choice(chars)
    return salt


def password_hash(password):
    salt = get_salt().encode('utf-8')
    h = hashlib.sha1(password.encode('utf-8'))
    h.update(salt)
    return "{SSHA}" + b64encode(h.digest() + salt).decode('utf-8')


def check_password(hashed_password, plain_password):
    """
     >>> hashed = password_hash('p4ssw0rD')
     >>> check_password(hashed, 'p4ssw0rD')
     True
     >>> check_password(hashed, 'p4ssw0rd')
     False

    """
    challenge_bytes = b64decode(hashed_password[6:].encode('utf-8'))
    digest = challenge_bytes[:20]
    salt = challenge_bytes[20:]
    hr = hashlib.sha1(plain_password.encode('utf-8'))
    hr.update(salt)
    return digest == hr.digest()


class CertificateEntryResponse(HttpResponse):
    def __init__(self, entry, **kwargs):
        pki = PKI()
        pki.ensure_certificate(entry)
        content = b''
        with open(entry.key_filename, 'rb') as fd:
            content += fd.read()
        with open(entry.crt_filename, 'rb') as fd:
            content += fd.read()
        with open(entry.ca_filename, 'rb') as fd:
            content += fd.read()
        super(CertificateEntryResponse, self).__init__(content=content, **kwargs)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
