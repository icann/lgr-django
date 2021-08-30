#! /bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from lgr_models.models.lgr import LgrBaseModel
from lgr_models.utils import get_model_from_url_name


class LgrModelConverter:
    regex = r'[a-zA-Z]+'

    def to_python(self, value):
        return get_model_from_url_name(value)

    def to_url(self, value):
        if isinstance(value, LgrBaseModel):
            return value.model_name.lower().replace('model', '')
        return value.lower().replace('model', '')
