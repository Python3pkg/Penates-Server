# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import OrderedDict
import datetime
import hashlib
import os
import re
from django.utils.timezone import utc

T61_RE = re.compile(r'^([A-Z][a-z]{2}) {1,2}(\d{1,2}) (\d{1,2}):(\d{1,2}):(\d{1,2}) (\d{4}).*$')


def force_bytestrings(unicode_list):
    """
     >>> force_bytestrings(['test'])
     ['test']
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
    >>> hostname_from_principal('HOST/test.example.org')
    u'test.example.org'
    >>> hostname_from_principal('HOST/test.example.org@TEST.EXAMPLE.ORG')
    u'test.example.org'
    """
    if not principal.startswith('HOST/'):
        raise ValueError
    return principal[5:].partition('@')[0]


def principal_from_hostname(hostname, realm):
    """
    >>> principal_from_hostname('test.example.org', 'TEST.EXAMPLE.ORG')
    u'HOST/test.example.org@TEST.EXAMPLE.ORG'
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
    >>> dhcp_list_to_dict(['key1 value11 value12', 'key2 value21 value22 value23'])
    OrderedDict([(u'key1', [u'value11', u'value12']), (u'key2', [u'value21', u'value22', u'value23'])])

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

    >>> dhcp_dict_to_list(dhcp_list_to_dict(['key1 value11 value12', 'key2 value21 value22 value23']))
    [u'key1 value11 value12', u'key2 value21 value22 value23']

    >>> dhcp_dict_to_list(dhcp_list_to_dict(['key1 value11 value12', 'key2 value21 value22 value23']))
    [u'key1 value11 value12', u'key2 value21 value22 value23']

    :rtype: :class:`list`
    """
    return ['%s %s' % (key, ' '.join(ensure_list(value))) for (key, value) in value_dict.items()]


def guess_use_ssl(scheme):
    use_ssl = False
    if scheme.endswith('s') and scheme != 'dns':
        scheme, use_ssl = scheme[:-1], True
    return scheme, use_ssl
