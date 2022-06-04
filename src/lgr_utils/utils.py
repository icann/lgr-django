#! /bin/env python
# -*- coding: utf-8 -*-
"""
utils - 
"""
import logging

logger = logging.getLogger(__name__)

LGR_CACHE_KEY_PREFIX = 'lgr-cache'


def get_all_subclasses_recursively(klass):
    subclasses = set()
    for subclass in klass.__subclasses__():
        subclasses.add(subclass)
        subclasses.update(get_all_subclasses_recursively(subclass))
    return subclasses
