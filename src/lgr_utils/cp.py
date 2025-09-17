import logging
from typing import Iterable

from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString, mark_safe
from lgr.char import CharBase, RangeChar
from lgr.utils import cp_to_str

logger = logging.getLogger(__name__)


def render_cp(char: CharBase) -> SafeString:
    """
    Render the code point(s) of a character.

    :param char: The char object to render.
    :returns: HTML string of the code points.
    """
    if isinstance(char, RangeChar):
        return mark_safe('U+{first_c} &hellip; U+{last_c}'.format(
            first_c=cp_to_str(char.first_cp),
            last_c=cp_to_str(char.last_cp)))
    else:
        return format_html_join(" ", "U+{}", ((cp_to_str(c),) for c in char.cp))


def render_name(char: CharBase, udata) -> SafeString:
    """
    Render the name of a char in HTML.

    :param char: The char object to render.
    :param udata: The Unicode data manager.
    :return: HTML string to display.
    """
    if isinstance(char, RangeChar):
        name = format_html(
            "{} &hellip; {}",
            udata.get_char_name(char.first_cp),
            udata.get_char_name(char.last_cp))
    else:
        name = format_html_join(" ", "{}", ((udata.get_char_name(cp),) for cp in char.cp))
    return name


def cp_to_slug(codepoint: Iterable[int]) -> str:
    """
    Convert a codepoint to a slug that can be used in URL.

    :param codepoint: Codepoint to convert.
    :return: Slug to be used in URL.
    """
    return '-'.join(str(c) for c in codepoint)
