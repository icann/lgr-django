#! /bin/env python
# -*- coding: utf-8 -*-
"""
utils - 
"""
import hashlib
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import force_bytes
from natsort import natsorted

from lgr_models.models.lgr import LgrBaseModel

logger = logging.getLogger('utils')


LGR_CACHE_TIMEOUT = 3600  # Cache timeout for serialized LGRs
LGR_OBJECT_CACHE_KEY = 'lgr-obj'
LGR_CACHE_KEY_PREFIX = 'lgr-cache'
LGR_REPERTOIRE_CACHE_KEY = 'repertoire'


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


def make_lgr_session_key(key, lgr: LgrBaseModel):
    key = f"{key}:{lgr.__class__.__name__}:{lgr.pk}"
    args = hashlib.md5(force_bytes(key))
    return "{}.{}".format(LGR_CACHE_KEY_PREFIX, args.hexdigest())


def clean_repertoire_cache(request, lgr_pk):
    """
    Clean all repertoire-related caches.

    :param request: Django request object
    :param lgr_id: a slug identifying the LGR
    :param uid: an unique ID under which the LGR is saved in session
    """
    cache.delete(make_lgr_session_key(LGR_REPERTOIRE_CACHE_KEY,
                                      request,
                                      lgr_pk))

