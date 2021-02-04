#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
api - 
"""
import logging

from django.conf import settings
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)

IDN_TABLES_SESSION_KEY = 'idn-table'


class LgrIcannSession:
    storage_location = settings.IDN_REVIEW_ICANN_OUTPUT_STORAGE_LOCATION

    def __init__(self, request):
        self.request = request

    def list_storage(self):
        """
        List files in the storage

        :return: the list of files in storage
        """
        storage = FileSystemStorage(location=self.storage_location)
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
        storage = FileSystemStorage(location=self.storage_location)
        return storage.open(filename, 'rb'), storage.size(filename)

    def storage_save_file(self, filename, data, mode=0o440):
        """
        Save a file in the storage

        :param filename: The name of the file to save
        :param data: The content of the file to save
        :param mode: File permissions mode
        """
        storage = FileSystemStorage(location=self.storage_location, file_permissions_mode=mode)
        return storage.save(filename, data)

    def storage_delete_file(self, filename):
        """
        Delete a file from the storage

        :param filename: The name of the file to delete
        """
        storage = FileSystemStorage(location=self.storage_location)
        try:
            storage.delete(filename)
        except NotImplementedError:
            # should not happen
            pass
