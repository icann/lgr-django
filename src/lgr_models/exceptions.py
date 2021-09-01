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


class LGRUnsupportedUnicodeVersionException(LGRException):
    """
    Raised when the unicode version in LGR is not supported by the tool
    """
    pass
