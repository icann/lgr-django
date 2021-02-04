#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
api - 
"""
import logging

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from lgr_session.api import LgrSession, LgrSerializer

logger = logging.getLogger(__name__)

IDN_TABLES_SESSION_KEY = 'idn-table'


class IdnTableInfo(LgrSerializer):
    def __init__(self, name, data):
        super(IdnTableInfo, self).__init__(name)
        self.data = data

    @classmethod
    def from_dict(cls, dct, **kwargs):
        return cls(dct['name'],
                   dct['data'])

    def to_dict(self):
        return {
            'name': self.name,
            'data': self.data
        }


class LgrIdnReviewSession(LgrSession):
    lgr_session_key = IDN_TABLES_SESSION_KEY
    lgr_serializer = IdnTableInfo
    storage_location = settings.IDN_REVIEW_USER_OUTPUT_STORAGE_LOCATION


def session_list_icann_idn_review_storage():
    """
    List files in the storage

    :return: the list of files in storage
    """
    storage = FileSystemStorage(location=settings.IDN_REVIEW_ICANN_OUTPUT_STORAGE_LOCATION)
    try:
        files = storage.listdir('.')
    except OSError:
        return []

    return sorted(files[1], reverse=True)
