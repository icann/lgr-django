#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
utils - 
"""
import hashlib
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import force_bytes
from django.utils.html import format_html_join, format_html
from django.utils.safestring import mark_safe
from natsort import natsorted

from lgr.char import RangeChar
from lgr.utils import cp_to_str

logger = logging.getLogger('utils')


def render_cp(char):
    """
    Render the code point(s) of a character.

    :param char: The char object to render.
    :returns: HTML string of the code points.
    """
    if isinstance(char, RangeChar):
        return mark_safe('U+{first_c} &hellip; U+{last_c}'.format(
            first_c=cp_to_str(char.first_cp),
            last_c=cp_to_str(char.last_cp),
        ))
    else:
        return format_html_join(" ", "U+{}",
                                ((cp_to_str(c),)
                                 for c in char.cp))


def render_name(char, udata):
    """
    Render the name of a char in HTML.

    :param char: The char object to render.
    :param udata: The Unicode data manager.
    :return: HTML string to display.
    """
    if isinstance(char, RangeChar):
        name = format_html("{} &hellip; {}",
                           udata.get_char_name(char.first_cp),
                           udata.get_char_name(char.last_cp))
    else:
        name = format_html_join(" ", "{}",
                                ((udata.get_char_name(cp),) for cp in char.cp))
    return name


def cp_to_slug(codepoint):
    """
    Convert a codepoint to a slug that can be used in URL.

    :param codepoint: Codepoint to convert.
    :return: Slug to be used in URL.
    """
    return '-'.join(str(c) for c in codepoint)


def list_files(location, startswith='', reverse=True):
    """
    List XML file in a given directory.

    :param location: Directory to list files from.
    :return: List of XML (.xml) files in this directory.
    """
    xml_files = []
    try:
        for file in os.listdir(location):
            if file.endswith(".xml") and file.startswith(startswith):
                xml_files.append(file.rsplit('.', 1)[0])
    except (OSError, IOError) as exc:
        logger.warning("Cannot access directory '%s': %s",
                       location, exc)
    return natsorted(xml_files, reverse=reverse)


def list_root_zones():
    """
    List XML LGR root zone files

    :return: List of root zone LGRs.
    """
    return list_files(settings.REPERTOIRE_STORAGE_LOCATION, startswith='lgr')


def list_built_in_lgr():
    """
    List XML LGR files stored at a specific location.

    :return: List of built-in LGRs.
    """
    return list_files(settings.LGR_STORAGE_LOCATION, reverse=False)


LGR_REPERTOIRE_CACHE_KEY = 'repertoire'


def make_lgr_session_key(key, request, lgr_id, uid=None):
    key = "{}:{}:{}".format(key, request.session.session_key, lgr_id)
    if uid:
        key += ':{}'.format(uid)
    args = hashlib.md5(force_bytes(key))
    return "{}.{}".format(LGR_CACHE_KEY_PREFIX, args.hexdigest())


def clean_repertoire_cache(request, lgr_id, uid=None):
    """
    Clean all repertoire-related caches.

    :param request: Django request object
    :param lgr_id: a slug identifying the LGR
    :param uid: an unique ID under which the LGR is saved in session
    """
    cache.delete(make_lgr_session_key(LGR_REPERTOIRE_CACHE_KEY,
                                      request,
                                      lgr_id, uid=uid))


LGR_CACHE_TIMEOUT = 3600  # Cache timeout for serialized LGRs
LGR_OBJECT_CACHE_KEY = 'lgr-obj'
LGR_CACHE_KEY_PREFIX = 'lgr-cache'
