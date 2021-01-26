# -*- coding: utf-8 -*-
"""
lgr_editor.py - Template tags for LGR editor
"""
from __future__ import unicode_literals

from django import template

from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from ..utils import render_char as render_char_lgr
from lgr.utils import format_cp as format_cp_utils

register = template.Library()


@register.filter()
def exc_to_text(exc):
    return lgr_exception_to_text(exc)


@register.filter()
def format_cp(cp):
    return format_cp_utils(cp)


@register.filter()
def format_char(char):
    return format_cp_utils(char.cp)


@register.filter()
def render_char(char):
    return render_char_lgr(char)
