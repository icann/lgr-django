# -*- coding: utf-8 -*-
"""
repertoires.py - functions for dealing with installed repertoires
"""

from __future__ import unicode_literals
import os
import logging
from django.conf import settings
from lgr.parser.xml_parser import XMLParser


logger = logging.getLogger(__name__)
REPERTOIRES = {}


def get_by_name(repertoire_name):
    if repertoire_name not in REPERTOIRES:
        logger.debug("%s parsing file", repertoire_name)
        with open(os.path.join(settings.REPERTOIRE_STORAGE_LOCATION, '{}.xml'.format(repertoire_name))) as f:
            parser = XMLParser(f, repertoire_name)
            REPERTOIRES[repertoire_name] = parser.parse_document()
    return REPERTOIRES[repertoire_name]
