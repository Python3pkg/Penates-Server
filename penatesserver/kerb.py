# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import subprocess
from django.conf import settings

__author__ = 'Matthieu Gallet'


def heimdal_command(*args):
    args_list = ['kadmin', '-p', settings.PENATES_PRINCIPAL, '-K', settings.PENATES_KEYTAB, ] + list(args)
    p = subprocess.Popen(args_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    return p


def mit_command(*args):
    arg_list = ['kadmin', '-p', settings.PENATES_PRINCIPAL, '-k', '-t', settings.PENATES_KEYTAB, '-q', ] + list(args)
    p = subprocess.Popen(arg_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    return p


def add_principal_to_keytab(principal, filename):
    if settings.RUNNING_TESTS:
        from penatesserver.models import PrincipalTest
        PrincipalTest.objects.get(name=principal)
        with codecs.open(filename, 'a', encoding='utf-8') as fd:
            fd.write(principal)
            fd.write('\n')
        return
    if settings.KERBEROS_IMPL == 'mit':
        mit_command('ktadd -k %s %s' % (filename, principal))
    else:
        heimdal_command('ext_keytab', '-k', filename, principal)


def change_password(principal, password):
    if settings.RUNNING_TESTS:
        from penatesserver.models import PrincipalTest
        PrincipalTest.objects.get(name=principal)
        return
    if settings.KERBEROS_IMPL == 'mit':
        mit_command('change_password -pw %s %s' % (password, principal))
    else:
        heimdal_command('passwd', '--password=%s' % password, principal)


def keytab_has_principal(principal, keytab_filename):
    if settings.RUNNING_TESTS:
        with codecs.open(keytab_filename, 'r', encoding='utf-8') as fd:
            content = fd.read()
        return principal in content.splitlines()
    if settings.KERBEROS_IMPL == 'mit':
        p = subprocess.Popen(['ktutil'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate('rkt %s\nlist' % keytab_filename)
    else:
        p = subprocess.Popen(['ktutil', '-k', keytab_filename, 'list'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
    if stderr:
        raise ValueError('Invalid keytab file %s' % keytab_filename)
    stdout_text = stdout.decode('utf-8')
    for line in stdout_text.splitlines():
        if line.strip().endswith(principal):
            return True
    return False


def add_principal(principal):
    if settings.RUNNING_TESTS:
        from penatesserver.models import PrincipalTest
        PrincipalTest.objects.get_or_create(name=principal)
        return
    from penatesserver.models import Principal
    if principal_exists(principal):
        return
    if settings.KERBEROS_IMPL == 'mit':
        Principal(name=principal).save()
    else:
        heimdal_command('add', '--random-key', '--max-ticket-life=1d', '--max-renewable-life=1w', '--attributes=',
                        '--expiration-time=never', '--pw-expiration-time=never', '--policy=default', principal)


def principal_exists(principal_name):
    if settings.RUNNING_TESTS:
        from penatesserver.models import PrincipalTest
        return PrincipalTest.objects.filter(name=principal_name).count() > 0
    from penatesserver.models import Principal
    if settings.KERBEROS_IMPL == 'mit':
        return bool(list(Principal.objects.filter(name=principal_name)[0:1]))
    else:
        p = heimdal_command('get', '-s', '-o', 'principal', principal_name)
        return p.returncode == 0


def delete_principal(principal):
    if settings.RUNNING_TESTS:
        from penatesserver.models import PrincipalTest
        PrincipalTest.objects.filter(name=principal).delete()
        return
    from penatesserver.models import Principal
    if settings.KERBEROS_IMPL == 'mit':
        Principal.objects.filter(name=principal).delete()
    else:
        heimdal_command('delete', principal)
