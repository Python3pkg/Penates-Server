# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from djangofloor.decorators import connect, SerializedForm

from django.template import RequestContext
__author__ = 'flanker'


@connect(path='penatesserver.test_signal')
def test_signal(request):
    return [{ 'signal': 'df.messages.warning', 'options': {'html': 'This is a server-side message', }, }]




if __name__ == '__main__':
    import doctest
    doctest.testmod()