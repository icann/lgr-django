# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from lgr_models.models.lgr import LgrBaseModel
from lgr_utils.utils import get_all_subclasses_recursively


class LgrModelConverter:
    regex = r'[a-zA-Z]+'
    __all_lgr_models = {}

    def to_python(self, value):
        if not self.__all_lgr_models:
            self.__all_lgr_models = {model.__name__.lower(): model for model in get_all_subclasses_recursively(LgrBaseModel)}
        return self.__all_lgr_models[value]

    def to_url(self, value):
        # convert the value to str data
        return value

