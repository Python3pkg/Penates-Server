# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import subprocess
from django.conf import settings

__author__ = 'Matthieu Gallet'


def heimdal_command(*args):
    args_list = ['kadmin', '-p', settings.PENATES_PRINCIPAL, '-K', settings.PENATES_KEYTAB, ] + list(args)
    p = subprocess.Popen(args_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    with open('/tmp/heimdal.log' % p.pid, 'ab') as fd:
        fd.write(b'----------------------------------------\n')
        fd.write(' '.join(args_list).encode('utf-8'))
        fd.write(b':\n')
        fd.write(stdout)
        fd.write(b'----------------------------------------\n')
        fd.write(stderr)
        fd.write(b'----------------------------------------\n')
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
    if principal_exists(principal):
        return
    if settings.KERBEROS_IMPL == 'mit':
        Principal(name=principal).save()
    else:
        heimdal_command('add', '--random-key', '--max-ticket-life=1d', '--max-renewable-life=1w', '--attributes=',
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
