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

logger = logging.getLogger(__name__)
REPERTOIRES = {}
SCRIPTS = {}


def get_by_name(repertoire_name):
    if repertoire_name not in REPERTOIRES:
        logger.debug("%s parsing file", repertoire_name)
        repertoire_path = os.path.join(settings.REPERTOIRE_STORAGE_LOCATION, '{}.xml'.format(repertoire_name))
        parser = XMLParser(repertoire_path, repertoire_name)
        doc = parser.parse_document()
        doc.expand_ranges()  # need to get through all code points
        REPERTOIRES[repertoire_name] = doc

    return REPERTOIRES[repertoire_name]


def get_all_scripts_from_repertoire(unicode_database):
    if unicode_database not in SCRIPTS:
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

        SCRIPTS[unicode_database] = scripts

    return SCRIPTS[unicode_database]
