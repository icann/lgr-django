#! /bin/env python
# -*- coding: utf-8 -*-
"""
signal.py - Signal used to handle folder deletion when a file is removed with django-cleanup
"""

import os


def delete_parent_folder(sender, **kwargs):
    try:
        os.rmdir(os.path.dirname(kwargs['file']))
    except:
        # if dir is not empty, do nothing
        pass
