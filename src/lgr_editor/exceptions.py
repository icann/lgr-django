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
