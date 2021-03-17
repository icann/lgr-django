# -*- coding: utf-8 -*-
"""
lgr_idn_table_review.py - Template tags for IDN table review
"""
from django import template

from lgr.utils import format_cp as format_cp_utils

register = template.Library()


@register.filter
def render_bool(boolean):
    return '✓' if boolean else '✕'

@register.filter
def render_general_rule(exists):
    if exists is None:
        return 'MANUAL_CHECK'
    return '✓' if exists else '✕'

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
