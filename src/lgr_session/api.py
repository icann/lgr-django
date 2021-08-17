#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import logging
import os
from abc import abstractmethod, ABC
from typing import Type

from django.core.files import File
from django.http import Http404

from lgr_advanced.lgr_editor.repertoires import get_by_name
from lgr_advanced.utils import list_root_zones, clean_repertoire_cache
from lgr_models.models.report import LGRReport

logger = logging.getLogger(__name__)


class LGRSerializer(ABC):

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


class LGRStorage:
    storage_model: Type[LGRReport] = None

    def __init__(self, user, filter_on_user=True):
        self.user = user
        self.filter_on_user = filter_on_user

    def _get_queryset(self, report_id=None, filename=None, pk=None):
        query_kwargs = {}
        if self.filter_on_user:
            query_kwargs['owner'] = self.user
        if pk:
            query_kwargs['pk'] = pk
        if report_id:
            query_kwargs['report_id'] = report_id
        if filename:
            # use get in case we sometime we have a file having the same ending as another file name, therefore we
            # would get an error instead of removing both files with no intention
            # For now this should never append the way report naming is
            query_kwargs['file__endswith'] = filename
        return self.storage_model.objects.filter(**query_kwargs).distinct()

    def list_storage(self, report_id=None, reverse=True, exclude=None):
        """
        List files in the storage

        :return: the list of files in storage
        """
        queryset = self._get_queryset(report_id=report_id)
        if reverse:
            queryset = queryset.reverse()
        if exclude:
            if not isinstance(exclude, (list, tuple)):
                exclude = [exclude]
            for ex in exclude:
                queryset = queryset.exclude(**ex)

        return queryset

    def storage_find_report_file(self, report_id, filename):
        """
        Find a file in the storage from its filename

        :param report_id: The ID of the report containing the file
        :param filename: The name of the file to be returned
        :return: A 2-tuple containing the File object and the file size
        """
        return self._get_queryset(report_id=report_id, filename=filename).get()

    def storage_get_report_file(self, report_pk):
        """
        Get a file in the storage

        :param report_pk: The report pk
        :return: A 2-tuple containing the File object and the file size
        """
        return self._get_queryset(pk=report_pk).get()

    def storage_save_report_file(self, filename, data, report_id=None):
        """
        Save a file in the storage

        :param filename: The name of the file to save for the report
        :param data: The content of the file to save
        :param report_id: The name of the report to save (defaults to filename without extension)
        """
        if not report_id:
            report_id = os.path.splitext(os.path.basename(filename))[0]
        obj = self.storage_model.objects.create(owner=self.user,
                                                report_id=report_id,
                                                file=File(data, name=filename))
        return obj

    def storage_delete_report(self, report_id):
        """
        Delete a file from the storage

        :param report_id: The ID of the report containing the file
        """
        self._get_queryset(report_id=report_id).delete()

    def storage_delete_report_file(self, report_pk):
        """
        Delete a file from the storage

        :param report_pk: The report pk
        """
        self._get_queryset(pk=report_pk).delete()

    def storage_can_read(self):
        """
        Check if user can read in storage.
        """
        return True


class LGRSession(LGRStorage):
    lgr_session_key: str = None
    lgr_serializer: Type[LGRSerializer] = None
    get_from_repertoire: bool = False
    loader_function = None  # function with session as first argument and repertoire as second

    def __init__(self, request):
        super(LGRSession, self).__init__(request.user)
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

        def get_lgr(known, _id, **serializer_kwargs):
            if _id not in known:
                raise Http404
            dct = known[_id]
            return self.lgr_serializer.from_dict(dct, **serializer_kwargs)

        known_lgrs = self.request.session.get(self.lgr_session_key, {})

        # handle RZ LGR selection
        if self.get_from_repertoire and lgr_id not in known_lgrs and lgr_id in list_root_zones():
            return self.lgr_serializer(lgr_id, lgr=get_by_name(lgr_id, with_unidb=True))

        if uid:
            if uid not in known_lgrs:
                raise Http404
            known_lgrs = known_lgrs[uid]

            return get_lgr(known_lgrs, lgr_id)

        lgr_serializer_kwargs = {'request': self.request}
        if self.loader_function:
            lgr_serializer_kwargs['lgr_loader_func'] = self.loader_function

        if lgr_set_id:
            if lgr_set_id not in known_lgrs:
                raise Http404
            lgr_dct = known_lgrs[lgr_set_id]
        else:
            return get_lgr(known_lgrs, lgr_id, **lgr_serializer_kwargs)

        if not lgr_dct.get('lgr_set_dct', None):
            raise Http404

        for lgr in lgr_dct.get('lgr_set_dct'):
            if lgr['name'] == lgr_id:
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
            self.request.session.setdefault(self.lgr_session_key, {})[lgr_id] = lgr_info.to_dict(self.request)
        else:
            self.request.session.setdefault(self.lgr_session_key, {}).setdefault(uid, {})[lgr_id] = lgr_info.to_dict(
                self.request)
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
        clean_repertoire_cache(self.request, lgr_id, uid=uid)
