# -*- coding: utf-8 -*-
"""
lgr_editor.py - Template tags for LGR editor
"""
from __future__ import unicode_literals

from django import template

from ..lgr_exceptions import lgr_exception_to_text
from ..utils import render_char as render_char_lgr
from lgr.utils import format_cp

register = template.Library()


@register.filter()
def exc_to_text(exc):
    return lgr_exception_to_text(exc)


@register.filter()
def format_char(char):
    return format_cp(char.cp)


@register.filter()
def render_char(char):
    return render_char_lgr(char)
