# -*- coding: utf-8 -*-
"""
repertoires.py - functions for dealing with installed repertoires
"""

from __future__ import unicode_literals

import logging

from django.core.cache import cache

from .utils import list_validating_repertoires

logger = logging.getLogger(__name__)
REPERTOIRE_CACHE_KEY = 'validating-repertoire'
SCRIPTS_CACHE_KEY = 'scripts'
CACHE_TIMEOUT = 3600 * 24 * 30


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
