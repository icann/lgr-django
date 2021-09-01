#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import logging
import os
from typing import Type

from django.core.files import File

from lgr_models.models.report import LGRReport

logger = logging.getLogger(__name__)


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
