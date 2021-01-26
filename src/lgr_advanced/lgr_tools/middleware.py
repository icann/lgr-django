# -*- coding: utf-8 -*-
# Author: Viagénie
"""
middleware - Implement some middlewares used by the whole app.
"""
from __future__ import unicode_literals

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect


class UnicodeDecodeErrorMiddleWare:
    """
    Simple middleware that takes care of UnicodeDecodeError.

    When a UnicodeDecodeError is thrown, this middleware will intercept it, add a message to notify
    the user to ensure its file(s) is/are correctly encoded, and will try to redirect them on the page they were.
    For the last part, we use the HTTP_REFERER. This might be a bit simplistic, but seems to work fine for now.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            if isinstance(e, UnicodeDecodeError):
                messages.error(request, _("Cannot decode input file. Make sure it is encoded in UTF-8"))
                return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            return response
