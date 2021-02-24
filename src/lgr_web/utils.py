#! /bin/env python
# -*- coding: utf-8 -*-
"""
utils - 
"""
import logging

from language_tags import data

logger = logging.getLogger(__name__)


def parse_language_registry():
    """
    Retrieve the list of languages and subtags from the IANA registry content.
    """
    languages = set()

    for ref in data.get('registry'):
        subtag = ref.get('Subtag')
        _type = ref.get("Type")
        script = ref.get("Suppress-Script")
        preferred = ref.get("Preferred-Value")
        deprecated = ref.get("Deprecated", False)
        # end of entry
        if not deprecated and _type == 'script':
            languages.add('und-' + subtag)
        elif not deprecated and subtag:
            languages.add(subtag)
            if script:
                languages.add('{}-{}'.format(subtag, script))
            if preferred:
                languages.add(preferred)
    return languages


IANA_LANG_REGISTRY = parse_language_registry()
