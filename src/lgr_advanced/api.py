#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import base64
import logging
from io import StringIO

from lgr.char import RangeChar
from lgr.exceptions import LGRException
from lgr.utils import format_cp
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
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


def copy_characters(lgr, input_lgr, validating_repertoire=None, force=False):
    nb_codepoints = 0
    for char in input_lgr.repertoire:
        char_len = 1
        add_fct = lambda c: lgr.add_cp(c.cp,
                                       comment=c.comment,
                                       ref=c.references,
                                       validating_repertoire=validating_repertoire,
                                       force=force)
        if isinstance(char, RangeChar):
            char_len = char.last_cp - char.first_cp + 1
            add_fct = lambda c: lgr.add_range(c.first_cp, c.last_cp,
                                              comment=c.comment,
                                              ref=c.references,
                                              validating_repertoire=validating_repertoire,
                                              force=force)
        try:
            add_fct(char)
            nb_codepoints += char_len
        except LGRException as exc:
            logger.warning("Cannot add code point '%s': %s",
                           format_cp(char.cp),
                           lgr_exception_to_text(exc))
        else:
            for variant in char.get_variants():
                try:
                    lgr.add_variant(char.cp,
                                    variant.cp,
                                    variant_type=variant.type,
                                    when=variant.when,
                                    not_when=variant.not_when,
                                    comment=variant.comment,
                                    ref=variant.references,
                                    validating_repertoire=validating_repertoire,
                                    force=force)
                except LGRException as exc:
                    logger.warning("Cannot add variant '%s' to "
                                   "code point '%s': %s",
                                   format_cp(variant.cp),
                                   format_cp(char.cp),
                                   lgr_exception_to_text(exc))
    return nb_codepoints