#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import logging
import os
from abc import abstractmethod, ABC
from typing import Type
from uuid import uuid4

from django.core.files.storage import FileSystemStorage
from django.http import Http404

from lgr_advanced.lgr_editor.repertoires import get_by_name
from lgr_advanced.utils import list_root_zones, clean_repertoire_cache

logger = logging.getLogger(__name__)


class LgrSerializer(ABC):

    def __init__(self, name, lgr=None, **kwargs):
        self.name = name
        self.lgr = lgr

    @classmethod
    @abstractmethod
    def from_dict(cls, dct, **kwargs):
        pass

    @abstractmethod
    def to_dict(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_xml(self, pretty_print=False, validate=False):
        pass


class LgrStorage:
    storage_location: str = None

    def get_storage_path(self, subfolder=None):
        """
        Get the storage path for the session

        :param subfolder: a subfolder for the path
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
        return os.path.join(self.storage_location, storage_key, subfolder or '')

    def list_storage(self, subfolder=None, reverse=True):
        """
        List files in the storage

        :param subfolder: a subfolder where to look for files
        :return: the list of files in storage
        """
        subfolder = subfolder or '.'
        storage = FileSystemStorage(location=self.get_storage_path())
        try:
            files = storage.listdir(subfolder)
        except OSError:
            return []

        return sorted(files[1], reverse=reverse)

    def list_storage_folders(self, subfolder=None):
        """
        List files in the storage

        :param subfolder: a subfolder where to look for files
        :return: the list of files in storage
        """
        storage = FileSystemStorage(location=self.get_storage_path(subfolder=subfolder))
        try:
            files = storage.listdir('.')
        except OSError:
            return []

        return sorted(files[0], reverse=True)

    def storage_get_file(self, filename, subfolder=None):
        """
        Get a file in the storage

        :param filename: The name of the file to be returned
        :param subfolder: a subfolder where to get the file
        :return: A 2-tuple containing the File object and the file size
        """
        storage = FileSystemStorage(location=self.get_storage_path(subfolder=subfolder))
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

    def storage_delete_file(self, filename, subfolder=None):
        """
        Delete a file from the storage

        :param subfolder: a subfolder where to delete the file
        :param filename: The name of the file to delete
        """
        storage = FileSystemStorage(location=self.get_storage_path(subfolder=subfolder))

        try:
            # if filename is a directory:
            #  - remove all directories in it
            for f in self.list_storage_folders(subfolder=os.path.join(subfolder or '', filename)):
                self.storage_delete_file(f, subfolder=os.path.join(subfolder or '', filename))
            #  - remove all files in it
            for f in self.list_storage(subfolder=os.path.join(subfolder or '', filename)):
                self.storage_delete_file(f, subfolder=os.path.join(subfolder or '', filename))
            storage.delete(filename)
        except NotImplementedError:
            # should not happen
            pass


class LgrSession(LgrStorage):
    lgr_session_key: str = None
    lgr_serializer: Type[LgrSerializer] = None
    get_from_repertoire: bool = False
    loader_function = None  # function with session as first argument and repertoire as second

    def __init__(self, request):
        self.request = request

    def list_lgr(self, uid=None):
        """
        List the LGRs stored in session.

        :param uid: an unique ID under which the LGR is saved in the session
        :return: list of `lgr_serializer` instances
        """
        known_lgrs = self.request.session.get(self.lgr_session_key, {})
        if uid:
            known_lgrs = known_lgrs.get(uid, {})
        return sorted(known_lgrs.values(), key=lambda x: x['name'])

    def open_lgr(self, lgr_id, data, **kwargs):
        """
        Parse the given LGR, and save it in session.

        :param lgr_id: a slug identifying the LGR
        :param data: a string with the data
        :param kwargs: The following kwargs are available for `LGRInfo` as `lgr_serializer`:
                         - validating_repertoire: optional name of a validating repertoire
                         - validate: if True, ensure the XML is valid LGR XML
                         - from_set: Whether the LGR belongs to a set or not
                         - lgr_set: The list of LGRInfo in the set if this is a merged LGR from a set
                         - set_label: The labels for the LGR set
                       The following kwargs are available for all:
                         - uid: An unique ID under which the LGR will be stored in the session
        :return: `lgr_serializer`
        """
        kwargs.update({
            'name': lgr_id,
            'data': data,
        })
        if 'lgr_set' in kwargs:
            kwargs['lgr_set_dct'] = [lgr.to_dict() for lgr in kwargs['lgr_set']]
        lgr_serializer_kwargs = {}
        if self.loader_function:
            lgr_serializer_kwargs = {'lgr_loader_func': self.loader_function}
        lgr_info = self.lgr_serializer.from_dict(kwargs, **lgr_serializer_kwargs)
        if not kwargs.get('from_set', False):
            # do not save lgr in session, it will be kept in set
            self.save_lgr(lgr_info, uid=kwargs.get('uid'))
        else:
            lgr_info.update_xml()

        return lgr_info

    def select_lgr(self, lgr_id, lgr_set_id=None, uid=None):
        """
        Find the LGR identified by `lgr_id` in the session.
        Can also retrieve a root zone LGR from repertoire if enabled.

        :param lgr_id: a slug identifying the LGR
        :param lgr_set_id: a slug identifying a LGR set if LGR is in a set
        :param uid: an unique ID under which the LGR is saved in the session
        :return: `lgr_serializer`
        """
        if lgr_set_id and uid:
            logger.error("Set either lgr_set_id or uid, not both")
            return Http404

        def get_lgr(known, _id):
            if _id not in known:
                raise Http404
            dct = known[_id]
            return self.lgr_serializer.from_dict(dct)

        known_lgrs = self.request.session.get(self.lgr_session_key, {})

        # handle RZ LGR selection
        if self.get_from_repertoire and lgr_id not in known_lgrs and lgr_id in list_root_zones():
            return self.lgr_serializer(lgr_id, lgr=get_by_name(lgr_id, with_unidb=True))

        if uid:
            if uid not in known_lgrs:
                raise Http404
            known_lgrs = known_lgrs[uid]

            return get_lgr(known_lgrs, lgr_id)

        if lgr_set_id:
            if lgr_set_id not in known_lgrs:
                raise Http404
            lgr_dct = known_lgrs[lgr_set_id]
        else:
            return get_lgr(known_lgrs, lgr_id)

        if not lgr_dct.get('lgr_set_dct', None):
            raise Http404

        for lgr in lgr_dct.get('lgr_set_dct'):
            if lgr['name'] == lgr_id:
                lgr_serializer_kwargs = {'request': self.request}
                if self.loader_function:
                    lgr_serializer_kwargs['lgr_loader_func'] = self.loader_function,
                return self.lgr_serializer.from_dict(lgr, **lgr_serializer_kwargs)
        raise Http404

    def save_lgr(self, lgr_info, lgr_id=None, uid=None):
        """
        Save the LGR object in session

        :param lgr_info: `lgr_serializer` instance
        :param lgr_id: a slug identifying the LGR
        :param uid: an unique ID under which the LGR is saved in the session
        """
        lgr_id = lgr_id if lgr_id is not None else lgr_info.name
        lgr_info.update_xml()  # make sure we have updated XML before saving
        if not uid:
            self.request.session.setdefault(self.lgr_session_key, {})[lgr_id] = lgr_info.to_dict()
        else:
            self.request.session.setdefault(self.lgr_session_key, {}).setdefault(uid, {})[lgr_id] = lgr_info.to_dict()
        # mark session as modified because we are possibly only changing the content of a dict
        self.request.session.modified = True
        # As LGR has been modified, need to invalidate the template repertoire cache
        clean_repertoire_cache(self.request, lgr_id, uid=uid)

    def delete_lgr(self, lgr_id, uid=None):
        """
        Delete the LGR object from session

        :param lgr_id: a slug identifying the LGR
        :param uid: an unique ID under which the LGR is saved in the session
        """
        try:
            if not uid:
                del self.request.session[self.lgr_session_key][lgr_id]
            else:
                del self.request.session[self.lgr_session_key][uid][lgr_id]
        except KeyError:
            raise Http404
        # mark session as modified because we are possibly only changing the content of a dict
        self.request.session.modified = True
        # Remove cached repertoire
        if self.get_from_repertoire:
            clean_repertoire_cache(self.request, lgr_id, uid=uid)
