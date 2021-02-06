#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
api - 
"""
import logging
from urllib.request import urlopen

import lxml.html
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from lgr.core import LGR
from lgr.tools.utils import download_file
from lgr_idn_table_review.admin.models import RefLgr
from lgr_idn_table_review.tool.api import IdnTableInfo

logger = logging.getLogger(__name__)

IDN_TABLES_SESSION_KEY = 'idn-table'
ICANN_URL = 'https://www.iana.org'
ICANN_IDN_TABLES = ICANN_URL + '/domains/idn-tables'


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


def get_icann_idn_repository_tables():
    tree = lxml.html.parse(urlopen(ICANN_IDN_TABLES))
    idn_table_urls = tree.xpath("//table[@id='idn-table']/tbody/tr/td/a/@href")
    for url in idn_table_urls:
        name, data = download_file(ICANN_URL + url)
        yield IdnTableInfo.from_dict({
            'name': name,
            'data': data.read().decode('utf-8'),
        })


def get_reference_lgr(idn_table_info: IdnTableInfo):
    idn_table: LGR = idn_table_info.lgr
    try:
        language_tag = idn_table.metadata.languages[0]
        logger.info('Retrieve reference LGR for IDN table %s with language tag %s', idn_table, language_tag)
        try:
            ref_lgr = RefLgr.objects.get(language_script=language_tag)
            logger.info('Found reference LGR %s from language tag', ref_lgr.name)
            return ref_lgr
        except RefLgr.DoesNotExist:
            logger.info("No reference LGR with language tag %s", language_tag)
    except IndexError:
        logger.info("No language tag in IDN table %s", idn_table)
        return None

    logger.info('Retrieve reference LGR for IDN table %s with script %s', idn_table, language_tag)

    try:
        script = idn_table.metadata.get_scripts()[0]
        logger.info('Retrieve reference LGR for IDN table % with script %s', idn_table, script)
        try:
            ref_lgr = RefLgr.objects.get(language_script=script)
            logger.info('Found script-based reference LGR %s', ref_lgr.name)
            return ref_lgr
        except RefLgr.DoesNotExist:
            logger.info('No reference LGR with script %s', script)
    except IndexError:
        logger.info("No script in IDN table %s", idn_table)
        return None

    return None
