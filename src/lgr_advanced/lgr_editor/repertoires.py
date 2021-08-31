# -*- coding: utf-8 -*-
"""
repertoires.py - functions for dealing with installed repertoires
"""

from __future__ import unicode_literals

import logging
import os

from django.conf import settings

from lgr.parser.xml_parser import XMLParser
from lgr_utils import unidb
from .utils import list_validating_repertoires

from django.core.cache import cache

logger = logging.getLogger(__name__)
REPERTOIRE_CACHE_KEY = 'validating-repertoire'
SCRIPTS_CACHE_KEY = 'scripts'
CACHE_TIMEOUT = 3600*24*30


def get_by_name(repertoire_name, with_unidb=False):
    repertoire_cache_key = "{}{}".format(REPERTOIRE_CACHE_KEY, repertoire_name).replace(' ', '')
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
    elif with_unidb:
        # need to retrieve unicode database as it is not retrieved from cache
        unicode_version = repertoire.metadata.unicode_version
        repertoire.unicode_database = unidb.manager.get_db_by_version(unicode_version)

    return repertoire


def get_all_scripts_from_repertoire(unicode_database):
    logger.debug("Get scripts for Unicode %s", unicode_database.get_unicode_version())
    scripts = dict()
    for validating_repertoire_object in list_validating_repertoires():
        vr_model, vr_pk = validating_repertoire_object.to_tuple()
        scripts_cache_key = f'{SCRIPTS_CACHE_KEY}:{unicode_database.get_unicode_version()}:{vr_model}:{vr_pk}'
        vr_scripts = cache.get(scripts_cache_key)
        if not vr_scripts:
            vr_scripts = set()
            logger.info(f'Scripts for {validating_repertoire_object.name} not in cache')
            validating_repertoire = validating_repertoire_object.to_lgr()
            for char in validating_repertoire.repertoire.all_repertoire():
                for cp in char.cp:
                    try:
                        # XXX: unicode version here may be different than validating repertoire one
                        vr_scripts.add(unicode_database.get_script(cp, alpha4=True))
                    except Exception as e:
                        logger.error('Get script failed for cp %s (validating repertoire: %s, unicode_database: %s) (%s)',
                                     cp, validating_repertoire,
                                     unicode_database.get_unicode_version(),
                                     e)

            cache.set(scripts_cache_key, vr_scripts, CACHE_TIMEOUT)

        scripts[(vr_model, vr_pk)] = vr_scripts

    return scripts
