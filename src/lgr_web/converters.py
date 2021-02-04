# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class BaseConverter:
    regex = None

    def to_python(self, value):
        # convert value to its corresponding python datatype
        return value

    def to_url(self, value):
        # convert the value to str data
        return value


class FileNameConverter(BaseConverter):
    regex = r'[\w\_\-\.]+'


class LgrSlugConverter(BaseConverter):
    regex = r'[\w\_\-\.]+'


class CodePointSlugConverter(BaseConverter):
    regex = r'[0-9a-z-A-Z]{1,6}(-[0-9a-z-A-Z]{1,6})*'


class VarSlugConverter(BaseConverter):
    regex = r'[0-9a-z-A-Z]{1,6}(-[0-9a-z-A-Z]{1,6})*,.*,.*'


class TagSlugConverter(BaseConverter):
    regex = r'[0-9a-zA-Z._:\-]+'


class ReferenceIdConverter(BaseConverter):
    regex = r'[\w\_\-\.\s\:]+'


class ActionIndexConverter(BaseConverter):
    regex = r'-?\d+'


class StorageTypeConverter(BaseConverter):
    regex = r'(tool|rev_usr|rev_icann)'
