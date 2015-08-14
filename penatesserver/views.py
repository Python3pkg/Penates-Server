# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.shortcuts import render_to_response
from django.template import RequestContext

__author__ = 'flanker'


def index(request):
    template_values = {}
    return render_to_response('penatesserver/index.html', template_values, RequestContext(request))


if __name__ == '__main__':
    import doctest

    doctest.testmod()
