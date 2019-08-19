# -*- coding: utf-8 -*-
"""
repertoires.py - functions for dealing with installed repertoires
"""

from __future__ import unicode_literals

import logging
import os

from django.conf import settings

from lgr.parser.xml_parser import XMLParser
from .utils import list_validating_repertoires
from . import unidb

from django.core.cache import cache

logger = logging.getLogger(__name__)
REPERTOIRE_CACHE_KEY = 'validating-repertoire'
SCRIPTS_CACHE_KEY = 'scripts'
CACHE_TIMEOUT = 3600*24*30


def get_by_name(repertoire_name, with_unidb=False):
    repertoire_cache_key = "{}{}".format(REPERTOIRE_CACHE_KEY, repertoire_name)
    repertoire = cache.get(repertoire_cache_key)
    logger.debug("Get repertoire by name %s", repertoire_name)
    if not repertoire:
        logger.info("%s parsing file as not in cache", repertoire_name)
        repertoire_path = os.path.join(settings.REPERTOIRE_STORAGE_LOCATION, '{}.xml'.format(repertoire_name))
        parser = XMLParser(repertoire_path, repertoire_name)
        if with_unidb:
            unicode_version = parser.unicode_version()
            parser.unicode_database = unidb.manager.get_db_by_version(unicode_version)
        repertoire = parser.parse_document()
        repertoire.expand_ranges()  # need to get through all code points
        cache.set(repertoire_cache_key, repertoire, CACHE_TIMEOUT)

    return repertoire


def get_all_scripts_from_repertoire(unicode_database):
    # XXX should we add database class name in cache key?
    scripts_cache_key = "{}:{}".format(SCRIPTS_CACHE_KEY, unicode_database.get_unicode_version())
    scripts = cache.get(scripts_cache_key)
    logger.debug("Get scripts for Unicode %s", unicode_database.get_unicode_version())
    if not scripts:
        logger.info("Scripts not in cache")
        scripts = set()
        for rep in list_validating_repertoires():
            validating_repertoire = get_by_name(rep)
            for char in validating_repertoire.repertoire.all_repertoire():
                for cp in char.cp:
                    try:
                        # XXX: unicode version here may be different than validating repertoire one
                        scripts.add(unicode_database.get_script(cp, alpha4=True))
                    except Exception as e:
                        logger.error('Get script failed for cp %s (validating repertoire: %s, unicode_database: %s) (%s)',
                                     cp, validating_repertoire,
                                     unicode_database.get_unicode_version(),
                                     e)

        cache.set(scripts_cache_key, scripts, CACHE_TIMEOUT)

    return scripts
