# -*- coding: utf-8 -*-
"""
exceptions.py - Define custom frontend exceptions.
"""


from lgr.exceptions import LGRException

class LGRValidationException(LGRException):
    """
    Raised when the XML validation against schema fails.
    """
    pass


class LGRInvalidLabelFileException(LGRException):
    """
    Raised when a label is invalid in a LGR
    """
    def __init__(self, label, message):
        super(LGRInvalidLabelFileException, self).__init__()
        self.label = label
        self.message = message
