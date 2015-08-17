# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import hashlib
import os
import re

from django.utils.timezone import utc

T61_RE = re.compile(r'^([A-Z][a-z]{2}) {1,2}(\d{1,2}) (\d{1,2}):(\d{1,2}):(\d{1,2}) (\d{4}).*$')


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


def file_sha1(filename):
    sha1 = hashlib.sha1()
    with open(filename, 'rb') as fd:
        sha1.update(fd.read())
    return sha1.hexdigest()
