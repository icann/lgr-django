#! /bin/env python
# -*- coding: utf-8 -*-
"""
storage
"""
import logging

from django.conf import settings
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)


class LGROverrideStorage(FileSystemStorage):

    def __init__(self, *args, **kwargs):
        if settings.DEFAULT_FILE_STORAGE != 'django.core.files.storage.FileSystemStorage':
            raise RuntimeError('Default storage has changed, please change LGROverrideStorage inheritance')
        super().__init__(*args, **kwargs)

    def get_alternative_name(self, file_root, file_ext):
        name = f'{file_root}{file_ext}'
        # as we want an alternative name, this likely means that the file exists, so remove it
        self.delete(name)
        return name

