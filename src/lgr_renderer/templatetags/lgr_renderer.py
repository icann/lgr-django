# -*- coding: utf-8 -*-
# Author: Viagénie
"""
lgr_renderer.py - Template tags for LGR renderer
"""
from django import template

register = template.Library()


@register.filter
def escape_newlines(value):
    """ Stupid filter to remove newline in an escaped HTML string."""
    return value.replace('\r', '').replace('\n', '')