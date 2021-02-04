#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
api - 
"""
import logging
import os
from functools import partial
from typing import Type
from uuid import uuid4

from django.core.files.storage import FileSystemStorage
from django.http import Http404

from lgr_advanced.lgr_editor.repertoires import get_by_name
from lgr_advanced.utils import list_root_zones, clean_repertoire_cache

logger = logging.getLogger(__name__)


class LgrSerializer:

    def __init__(self, name, **kwargs):
        self.name = name

    @classmethod
    def from_dict(cls, dct, **kwargs):
        raise NotImplementedError

    def to_dict(self, *args, **kwargs):
        raise NotImplementedError

    def update_xml(self, pretty_print=False, validate=False):
        raise NotImplementedError


class LgrSession:
    lgr_session_key: str = None
    lgr_serializer: Type[LgrSerializer] = None
    get_from_repertoire: bool = False
    storage_location: str = None
    loader_function = None

    def __init__(self, request):
        self.request = request

    def list_lgr(self):
        """
        List the LGRs stored in session.

        :return: list of `lgr_serializer` instances
        """
        known_lgrs = self.request.session.get(self.lgr_session_key, {})
        return sorted(known_lgrs.values(), key=lambda x: x['name'])

    def delete_all(self):
        """
        Delete the LGRs stored in session.
        """
        self.request.session.pop(self.lgr_session_key, None)

    def open_lgr(self, lgr_id, lgr_xml, **kwargs):
        """
        Parse the given LGR in XML format, and save it in session.

        :param lgr_id: a slug identifying the LGR
        :param lgr_xml: a string with the xml
        :param kwargs: The following kwargs are available for `LGRInfo` as `lgr_serializer`:
                         - validating_repertoire_name: optional name of a validating repertoire
                         - validate: if True, ensure the XML is valid LGR XML
                         - from_set: Whether the LGR belongs to a set or not
                         - lgr_set: The list of LGRInfo in the set if this is a merged LGR from a set
                         - set_label: The labels for the LGR set
        :return: `lgr_serializer`
        """
        kwargs.update({
            'name': lgr_id,
            'data': lgr_xml,
        })
        if 'lgr_set' in kwargs:
            kwargs['lgr_set_dct'] = [lgr.to_dict() for lgr in kwargs['lgr_set']]
        lgr_serializer_kwargs = {}
        if self.loader_function:
            lgr_serializer_kwargs = {'lgr_loader_func': partial(self.loader_function, session=self)}
        lgr_info = self.lgr_serializer.from_dict(**kwargs, **lgr_serializer_kwargs)
        if not kwargs.get('from_set', False):
            # do not save lgr in session, it will be kept in set
            self.save_lgr(lgr_info)
        else:
            lgr_info.update_xml()

        return lgr_info

    def select_lgr(self, lgr_id, lgr_set_id=None):
        """
        Find the LGR identified by `lgr_id` in the session.
        Can also retrieve a root zone LGR from repertoire if enabled.

        :param lgr_id: a slug identifying the LGR
        :param lgr_set_id: a slug identifying a LGR set if LGR is in a set
        :return: `lgr_serializer`
        """
        known_lgrs = self.request.session.get(self.lgr_session_key, {})

        # handle RZ LGR selection
        if self.get_from_repertoire and lgr_id not in known_lgrs and lgr_id in list_root_zones():
            return self.lgr_serializer(lgr_id, lgr=get_by_name(lgr_id, with_unidb=True))

        if lgr_set_id:
            if lgr_set_id not in known_lgrs:
                raise Http404
            lgr_dct = known_lgrs[lgr_set_id]
        else:
            if lgr_id not in known_lgrs:
                raise Http404
            lgr_dct = known_lgrs[lgr_id]
            return self.lgr_serializer.from_dict(lgr_dct)

        if not lgr_dct.get('lgr_set_dct', None):
            raise Http404

        for lgr in lgr_dct.get('lgr_set_dct'):
            if lgr['name'] == lgr_id:
                lgr_serializer_kwargs = {'request': self.request}
                if self.loader_function:
                    lgr_serializer_kwargs['lgr_loader_func'] = partial(self.loader_function, session=self),
                return self.lgr_serializer.from_dict(lgr, **lgr_serializer_kwargs)
        raise Http404

    def save_lgr(self, lgr_info, lgr_id=None):
        """
        Save the LGR object in session

        :param lgr_info: `lgr_serializer` instance
        :param lgr_id: a slug identifying the LGR
        """
        lgr_id = lgr_id if lgr_id is not None else lgr_info.name
        lgr_info.update_xml()  # make sure we have updated XML before saving
        self.request.session.setdefault(self.lgr_session_key, {})[lgr_id] = lgr_info.to_dict()
        # mark session as modified because we are possibly only changing the content of a dict
        self.request.session.modified = True
        # As LGR has been modified, need to invalidate the template repertoire cache
        clean_repertoire_cache(self.request, lgr_id)

    def delete_lgr(self, lgr_id):
        """
        Delete the LGR object from session

        :param lgr_id: a slug identifying the LGR
        """
        try:
            del self.request.session[self.lgr_session_key][lgr_id]
        except KeyError:
            raise Http404
        # mark session as modified because we are possibly only changing the content of a dict
        self.request.session.modified = True
        # Remove cached repertoire
        if self.get_from_repertoire:
            clean_repertoire_cache(self.request, lgr_id)

    def get_storage_path(self):
        """
        Get the storage path for the session

        :return: the storage location
        """
        # get or create a key for storage in the session,
        try:
            storage_key = self.request.session['storage']
        except KeyError:
            # generate a random key
            storage_key = uuid4().hex
            self.request.session['storage'] = storage_key
        # the storage may still not be created here but now it has a path for
        #  this session
        return os.path.join(self.storage_location, storage_key)

    def list_storage(self):
        """
        List files in the storage

        :return: the list of files in storage
        """
        storage = FileSystemStorage(location=self.get_storage_path())
        try:
            files = storage.listdir('.')
        except OSError:
            return []

        return sorted(files[1], reverse=True)

    def storage_get_file(self, filename):
        """
        Get a file in the storage

        :param filename: The name of the file to be returned
        :return: A 2-tuple containing the File object and the file size
        """
        storage = FileSystemStorage(location=self.get_storage_path())
        return storage.open(filename, 'rb'), storage.size(filename)

    def storage_save_file(self, filename, data, mode=0o440):
        """
        Save a file in the storage

        :param filename: The name of the file to save
        :param data: The content of the file to save
        :param mode: File permissions mode
        """
        storage = FileSystemStorage(location=self.get_storage_path(), file_permissions_mode=mode)
        return storage.save(filename, data)

    def storage_delete_file(self, filename):
        """
        Delete a file from the storage

        :param filename: The name of the file to delete
        """
        storage = FileSystemStorage(location=self.get_storage_path())
        try:
            storage.delete(filename)
        except NotImplementedError:
            # should not happen
            pass
