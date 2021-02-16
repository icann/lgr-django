#! /bin/env python
# -*- coding: utf-8 -*-
"""
api
"""
import logging

from language_tags import tags
from pycountry import languages

logger = logging.getLogger('api')


def tag_to_language_script(tag):
    # replace 3 char language isocode by 2 char isocode
    # XXX Assume lang-script format
    splitted = tag.split('-', 1)
    lang = splitted[0]
    try:
        lang_lookup = languages.lookup(lang)
        lang_2 = lang_lookup.alpha_2
    except (LookupError, AttributeError):
        lang_2 = lang

    splitted[0] = lang_2
    tag = '-'.join(splitted)

    tag = tags.tag(tag)
    language = str(tag.language) if tag.language else ''
    if language.lower() == 'und':
        language = ''

    script = str(tag.script) if tag.script else ''

    return language, script
