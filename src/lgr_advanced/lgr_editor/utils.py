# -*- coding: utf-8 -*-
"""
utils.py - utility functions for LGR Editor.
"""
import logging
from urllib.parse import quote_plus

from django.utils.html import mark_safe, format_html, format_html_join

from lgr.char import RangeChar
from lgr.utils import cp_to_str
from lgr_utils.cp import cp_to_slug

HTML_UNICODE_FORMAT = '<bdi>&#x%06X;</bdi>'

logger = logging.getLogger(__name__)


def render_char(char):
    """
    Render a char in HTML.

    Input:
        * char: The char object to render.
    Output:
        * HTML string to display
    """
    if isinstance(char, RangeChar):
        return mark_safe('U+{first_c} ({first_u}) &hellip; '
                         'U+{last_c} ({last_u})'.format(
            first_c=cp_to_str(char.first_cp),
            first_u=HTML_UNICODE_FORMAT % char.first_cp,
            last_c=cp_to_str(char.last_cp),
            last_u=HTML_UNICODE_FORMAT % char.last_cp,
        ))
    else:
        out = format_html_join(" ", "U+{} ({})", ((cp_to_str(c), mark_safe(HTML_UNICODE_FORMAT % c)) for c in char.cp))
        if len(char.cp) > 1:
            out += mark_safe(" [<bdi>{}</bdi>]".format("".join("&#x{:06X};".format(c) for c in char.cp)))
        return out


def render_cp_or_sequence(cp_or_sequence):
    """
    Render the code point(s) of a list unique or list of code points..

    :param cp_or_sequence: Sequence of code point to add to the class.
    :returns: HTML string of the code point sequence
    """
    if isinstance(cp_or_sequence, int):
        cp_or_sequence = [cp_or_sequence]

    out = format_html_join(" ", "U+{} ({})",
                           ((cp_to_str(c), mark_safe(HTML_UNICODE_FORMAT % c)) for c in cp_or_sequence))
    if len(cp_or_sequence) > 1:
        out += mark_safe(" [<bdi>{}</bdi>]".format("".join("&#x{:06X};".format(c) for c in cp_or_sequence)))
    return out


def render_age(char, udata):
    """
    Render the age of a char in HTML.

    :param char: The char object to render.
    :param udata: The Unicode data manager.
    :return: HTML string to display.
    """
    if isinstance(char, RangeChar):
        name = format_html("{} &hellip; {}",
                           udata.get_char_age(char.first_cp),
                           udata.get_char_age(char.last_cp))
    else:
        name = format_html_join(" ", "{}",
                                ((udata.get_char_age(cp),) for cp in char.cp))
    return name


def var_to_slug(variant):
    """
    Convert a variant to a slug that can be used in URL.

    :param variant: Variant to convert.
    :return: Slug to be used in URL.
    """
    return '{},{},{}'.format(cp_to_slug(variant.cp),
                             quote_plus(variant.when or ''),
                             quote_plus(variant.not_when or ''))


def slug_to_cp(cp_slug):
    """
    Convert a slug to a codepoint.

    :param cp_slug: Slug from URL.
    :return: Codepoint iterable to be used.
    """
    return tuple(int(c) for c in cp_slug.split('-'))


def slug_to_var(var_slug):
    """
    Convert a slug to a var.

    :param var_slug: Slug from URL in the form of var_cp,when,not-when
    :return: Codepoint iterable to be used.
    """
    cp_slug, var_when, var_not_when = var_slug.split(',')
    return slug_to_cp(cp_slug), var_when, var_not_when
