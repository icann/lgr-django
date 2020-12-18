# -*- coding: utf-8 -*-
"""
lgr_editor.py - Template tags for LGR editor
"""
from __future__ import unicode_literals

from django import template

from lgr.utils import format_cp as format_cp_utils

register = template.Library()


@register.filter
def render_bool(boolean):
    return '✓' if boolean else '✕'


@register.filter
def format_cp(cp):
    return format_cp_utils(cp)


@register.filter
def format_cp_list(cps):
    if not cps:
        return ''
    return ', '.join(format_cp_utils(cp) for cp in cps)


@register.filter
def format_glyph_list(glyphs):
    return ', '.join(glyphs)
