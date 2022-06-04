#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import base64
import logging
from io import StringIO

from lgr_advanced.lgr_tools.models import LGRToolReport
from lgr_session.api import LGRStorage

logger = logging.getLogger(__name__)

OLD_LGR_NS = 'http://www.iana.org/lgr/0.1'


class LabelInfo(object):

    def __init__(self, name, labels=None, data=None):
        self.name = name
        self.labels = labels
        self.data = data

    @classmethod
    def from_dict(cls, dct):
        return cls(dct['name'],
                   StringIO(base64.b64decode(dct['data']).decode('utf-8')),
                   dct['data'])

    @classmethod
    def from_form(cls, name, label_input):
        data = label_input.decode('utf-8')
        labels = StringIO(data)
        b64data = base64.b64encode(label_input).decode('utf-8')

        return cls(name, labels, b64data)

    @classmethod
    def from_list(cls, name, labels):
        data = '\n'.join(labels)
        labels = StringIO(data)
        b64data = base64.b64encode(data.encode('utf-8')).decode('utf-8')

        return cls(name, labels, b64data)

    def to_dict(self):
        return {
            'name': self.name,
            'data': self.data
        }


class LGRToolStorage(LGRStorage):
    storage_model = LGRToolReport
