#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
api - 
"""
import logging
from io import BytesIO

from django.conf import settings

from lgr.parser.heuristic_parser import HeuristicParser
from lgr.parser.xml_parser import LGR_NS
from lgr_advanced import unidb
from lgr_advanced.api import OLD_LGR_NS
from lgr_session.api import LgrSession, LgrSerializer

logger = logging.getLogger(__name__)

IDN_TABLES_SESSION_KEY = 'idn-table'


class IdnTableInfo(LgrSerializer):
    def __init__(self, name, data, lgr):
        super(IdnTableInfo, self).__init__(name, lgr=lgr)
        self.data = data

    @classmethod
    def from_dict(cls, dct, **kwargs):
        data = dct['data']
        # Replace old namespace by the new one for compatibility purpose with old LGR
        data = data.replace(OLD_LGR_NS, LGR_NS)
        return cls(dct['name'],
                   dct['data'],
                   lgr=cls._parse_idn_table_as_lgr(dct['name'], data))

    def to_dict(self):
        return {
            'name': self.name,
            'data': self.data,
        }

    def update_xml(self, pretty_print=False, validate=False):
        pass

    @classmethod
    def _parse_idn_table_as_lgr(cls, name, data):
        parser = HeuristicParser(BytesIO(data.encode('utf-8')), name)

        # Actually parse document
        lgr = parser.parse_document()

        # Retrieve Unicode version to set appropriate Unicode database
        unicode_version = lgr.metadata.unicode_version
        lgr.unicode_database = unidb.manager.get_db_by_version(unicode_version)
        return lgr


class LgrIdnReviewSession(LgrSession):
    lgr_session_key = IDN_TABLES_SESSION_KEY
    lgr_serializer = IdnTableInfo
    storage_location = settings.IDN_REVIEW_USER_OUTPUT_STORAGE_LOCATION
