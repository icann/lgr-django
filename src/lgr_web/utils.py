#! /bin/env python
# -*- coding: utf-8 -*-
"""
utils - 
"""
import logging

from language_tags import data

logger = logging.getLogger(__name__)

# all types: {'redundant', 'extlang', 'script', 'grandfathered', 'language', 'region', 'variant'}
IGNORE_LANGUAGE_REGISTRY_TYPES = ['region', 'variant']


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
        if _type in IGNORE_LANGUAGE_REGISTRY_TYPES:
            continue
        if deprecated:
            continue
        if _type == 'script':
            languages.add('und-' + subtag)
        elif subtag:
            languages.add(subtag)
            if script:
                languages.add('{}-{}'.format(subtag, script))
            if preferred:
                languages.add(preferred)
    return languages


IANA_LANG_REGISTRY = parse_language_registry()
