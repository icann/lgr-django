#! /bin/env python
# -*- coding: utf-8 -*-
"""
utils - 
"""
import logging

logger = logging.getLogger(__name__)


def get_all_subclasses_recursively(klass):
    subclasses = set()
    for subclass in klass.__subclasses__():
        subclasses.add(subclass)
        subclasses.update(get_all_subclasses_recursively(subclass))
    return subclasses
