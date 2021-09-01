#! /bin/env python
# -*- coding: utf-8 -*-
"""
utils - 
"""
import logging
import os

from django.conf import settings
from natsort import natsorted

logger = logging.getLogger('utils')

LGR_CACHE_KEY_PREFIX = 'lgr-cache'


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


def list_built_in_lgr():
    """
    List XML LGR files stored at a specific location.

    :return: List of built-in LGRs.
    """
    return list_files(settings.LGR_STORAGE_LOCATION, reverse=False)
