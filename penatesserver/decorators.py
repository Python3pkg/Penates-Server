# -*- coding=utf-8 -*-


from django.conf import settings

from djangofloor.exceptions import PermissionDenied

__author__ = 'mgallet'


def admin_required(function=None):
    """Decorator that checks the "admin_token" parameter in the GET array"""

    def wrapper(view):
        def actual_decorator(request, *args, **kwargs):
            if request.GET.get(settings.PENATES_ADMIN_TOKEN_PARAMETER, '') != settings.PENATES_ADMIN_TOKEN:
                raise PermissionDenied()
            return view(request, *args, **kwargs)

        return actual_decorator

    if function is None:
        return wrapper
    return wrapper(function)
