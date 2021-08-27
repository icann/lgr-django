#! /bin/env python
# -*- coding: utf-8 -*-
"""
utils - 
"""
import logging

from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from lgr.char import RangeChar
from lgr_advanced.lgr_editor.utils import HTML_UNICODE_FORMAT

logger = logging.getLogger('utils')


def render_glyph(char):
    """
    Render the glyph corresponding to a char in HTML.

    :param char: The char object to render.
    :returns: HTML string of the glyph.
    """
    if isinstance(char, RangeChar):
        return mark_safe('{first_u} &hellip; {last_u}'.format(
            first_u=HTML_UNICODE_FORMAT % char.first_cp,
            last_u=HTML_UNICODE_FORMAT % char.last_cp,
        ))
    else:
        out = format_html_join(" ", "{}",
                               ((mark_safe(HTML_UNICODE_FORMAT % c),)
                                for c in char.cp))
        if len(char.cp) > 1:
            out += mark_safe(" [<bdi>{}</bdi>]".format("".join("&#x{:06X};".format(c) for c in char.cp)))
        return out