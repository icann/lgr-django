# -*- coding: utf-8 -*-
"""
lgr_auth.py - Template tags for LGR auth
"""
from __future__ import unicode_literals

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def oauth_logo(backend_name):
    return f"chrome/img/oauth/{backend_name.split('-')[0]}.png"


@register.filter
@stringfilter
def oauth_name(backend_name):
    return backend_name.split('-')[0]
