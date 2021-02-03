#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
api - 
"""
import logging
import os
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import Http404

logger = logging.getLogger(__name__)

IDN_TABLES_SESSION_KEY = 'idn-table'


class IdnTableInfo(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data

    @classmethod
    def from_dict(cls, dct):
        return cls(dct['name'],
                   dct['data'])

    def to_dict(self):
        return {
            'name': self.name,
            'data': self.data
        }


def session_list_idn_tables(request):
    """
    List the LGRs stored in session.

    :param request: Django request object
    :return: list of `IdnTableInfo` instances
    """
    known_lgrs = request.session.get(IDN_TABLES_SESSION_KEY, {})
    return sorted(known_lgrs.values(), key=lambda x: x['name'])


def session_delete_idn_tables(request):
    """
    Delete the LGRs stored in session.

    :param request: Django request object
    """
    request.session.pop(IDN_TABLES_SESSION_KEY, None)


def session_open_idn_table(request, idn_table_id, data):
    """
    Parse the given LGR in XML format, and save it in session.

    :param request: Django request object
    :param idn_table_id: a slug identifying the IDN table
    :param data: a string with the idn table content
    :return: `IdnTableInfo`
    """
    idn_table_info = IdnTableInfo(idn_table_id, data)
    session_save_idn_table(request, idn_table_info)
    return idn_table_info


def session_select_idn_table(request, idn_table_id):
    """
    Find the IDN table identified by `idn_table_id` in the session.
    Can also retrieve a root zone LGR.

    :param request: Django request object
    :param idn_table_id: a slug identifying the IDN table
    :return: `IdnTableInfo`
    """
    known_idn_tables = request.session.get(IDN_TABLES_SESSION_KEY, {})

    if idn_table_id not in known_idn_tables:
        raise Http404
    idn_table_dct = known_idn_tables[idn_table_id]
    return IdnTableInfo.from_dict(idn_table_dct)


def session_save_idn_table(request, idn_table_info):
    """
    Save the LGR object in session
    :param request: Django request object
    :param idn_table_info: `IdnTableInfo` instance
    """
    idn_table_id = idn_table_info.name
    request.session.setdefault(IDN_TABLES_SESSION_KEY, {})[idn_table_id] = idn_table_info.to_dict()
    # mark session as modified because we are possibly only changing the content of a dict
    request.session.modified = True


def session_get_user_idn_review_storage(request):
    """
    Get the storage path for the session

    :param request: Django request object
    :return: the storage location
    """
    # get or create a key for storage in the session,
    try:
        storage_key = request.session['storage']
    except KeyError:
        # generate a random key
        storage_key = uuid4().hex
        request.session['storage'] = storage_key
    # the storage may still not be created here but now it has a path for
    #  this session
    return os.path.join(settings.IDN_REVIEW_USER_OUTPUT_STORAGE_LOCATION,
                        storage_key)


def session_list_user_id_review_storage(request):
    """
    List files in the storage

    :param request: Django request object
    :return: the list of files in storage
    """
    storage = FileSystemStorage(location=session_get_user_idn_review_storage(request))
    try:
        files = storage.listdir('.')
    except OSError:
        return []

    return sorted(files[1], reverse=True)


def session_get_user_idn_review_file(request, filename):
    """
    Get a file in the storage

    :param request: Django request object
    :param filename: The name of the file to be returned
    :return: A 2-tuple containing the File object and the file size
    """
    storage = FileSystemStorage(location=session_get_user_idn_review_storage(request))
    return storage.open(filename, 'rb'), storage.size(filename)


def session_save_user_idn_review_file(request, filename, data):
    storage = FileSystemStorage(location=session_get_user_idn_review_storage(request))
    storage.save(filename, data)


