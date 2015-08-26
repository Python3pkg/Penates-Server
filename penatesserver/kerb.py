# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import subprocess
from django.conf import settings

__author__ = 'Matthieu Gallet'


def heimdal_command(*args):
    p = subprocess.Popen(['kadmin', '-p', settings.PENATES_PRINCIPAL, '-K', settings.PENATES_KEYTAB, ] + list(args), stdout=subprocess.PIPE)
    p.communicate()
    return p


def add_principal_to_keytab(principal, filename):
    if settings.KERBEROS_IMPL == 'mit':
        p = subprocess.Popen(['kadmin', '-p', settings.PENATES_PRINCIPAL, '-k', '-t', settings.PENATES_KEYTAB, '-q', 'ktadd -k %s %s' % (filename, principal)], stdout=subprocess.PIPE)
        p.communicate()
    else:
        heimdal_command('ext_keytab', '-k', filename, principal)


def change_password(principal, password):
    if settings.KERBEROS_IMPL == 'mit':
        p = subprocess.Popen(['kadmin', '-p', settings.PENATES_PRINCIPAL, '-k', '-t', settings.PENATES_KEYTAB, '-q', 'change_password -pw %s %s' % (password, principal)])
        p.communicate()
    else:
        heimdal_command('passwd', '--password=%s' % password, principal)


def keytab_has_principal(principal, keytab_filename):
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
    from penatesserver.models import Principal
    if settings.KERBEROS_IMPL == 'mit':
        if Principal.objects.filter(name=principal).count() == 0:
            Principal(name=principal).save()
    else:
        heimdal_command('add', '--random-password', '--max-ticket-life=1d', '--max-renewable-life=1w', '--attributes=',
                        '--expiration-time=never', '--pw-expiration-time=never', '--policy=default', principal)


def principal_exists(principal_name):
    from penatesserver.models import Principal
    if settings.KERBEROS_IMPL == 'mit':
        return bool(list(Principal.objects.filter(name=principal_name)[0:1]))
    else:
        p = heimdal_command('get', '-s', '-o', 'principal', principal_name)
        return p.returncode == 0


def delete_principal(principal):
    from penatesserver.models import Principal
    if settings.KERBEROS_IMPL == 'mit':
        Principal.objects.filter(name=principal).delete()
    else:
        heimdal_command('delete', principal)
