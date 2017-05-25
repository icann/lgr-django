# -*- coding: utf-8 -*-
"""
lgr_exceptions.py - Map LGR exception to user terms.
"""
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

import lgr.exceptions
import exceptions
from lgr.utils import format_cp


def lgr_exception_to_text(exception):
    """
    Convert an LGR exception to a (translatable) string.

    Input:
        * exception: The LGR exception.
    Output:
       * The string to use in a Message
    """

    message = ''
    if isinstance(exception, lgr.exceptions.NotInLGR):
        message = _('Input code point %(codepoint)s is not in the LGR') % {
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.NotInRepertoire):
        message = _('Input code point %(codepoint)s is not in '
                    'the reference repertoire') % {
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.VariantAlreadyExists):
        message = _('Variant %(variant_codepoint)s already exists for '
                    'code point %(codepoint)s') % {
            'variant_codepoint': format_cp(exception.variant),
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.RangeAlreadyExists):
        message = _('Range %(first_cp)s - %(last_cp)s already exists in the LGR') % {
            'first_cp': format_cp(exception.first_cp),
            'last_cp': format_cp(exception.last_cp)
        }
    elif isinstance(exception, lgr.exceptions.CharAlreadyExists):
        message = _('Input code point %(codepoint)s already exists '
                    'in the LGR') % {
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.CharNotInScript):
        message = _('Input code point %(codepoint)s is not in LGR script') % {
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.CharInvalidIdnaProperty):
        message = _('Input code point %(codepoint)s is not a '
                    'PVALID/CONTEXTO/CONTEXTJ code point per IDNA2008') % {
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.CharInvalidContextRule):
        message = _('Code point %(codepoint)s has invalid context rule') % {
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.RangeInvalidContextRule):
        message = _('Range %(first_cp)s - %(last_cp)s has invalid context rule') % {
            'first_cp': format_cp(exception.first_cp),
            'last_cp': format_cp(exception.last_cp)
        }
    elif isinstance(exception, lgr.exceptions.VariantInvalidContextRule):
        message = _('Variant %(variant_codepoint)s of code point %(codepoint)s'
                    'has invalid context rule') % {
            'variant_codepoint': format_cp(exception.variant),
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.DuplicateReference):
        message = _('Duplicate reference for code point %(codepoint)s') % {
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.CharLGRException):
        message = _('Unspecified exception for input code point '
                    '%(codepoint)s') % {
            'codepoint': format_cp(exception.cp)
        }
    elif isinstance(exception, lgr.exceptions.LGRFormatException):
        reason = exception.reason
        if reason == lgr.exceptions.LGRFormatException.LGRFormatReason.INVALID_DATE_TAG:
            message = _('Invalid date value')
        elif reason == lgr.exceptions.LGRFormatException.LGRFormatReason.INVALID_LANGUAGE_TAG:
            message = _('Invalid language')
        elif reason == lgr.exceptions.LGRFormatException.LGRFormatReason.INVALID_UNICODE_VERSION_TAG:
            message = _('Invalid Unicode version')
        else:
            message = _('Invalid LGR XML file')
    elif isinstance(exception, lgr.exceptions.ReferenceNotDefined):
        message = _('Reference %(ref_id)s is not defined') % {
            'ref_id': exception.ref_id
        }
    elif isinstance(exception, lgr.exceptions.ReferenceAlreadyExists):
        message = _('Reference %(ref_id)s already exists') % {
            'ref_id': exception.ref_id
        }
    elif isinstance(exception, lgr.exceptions.RuleError):
        message = _('Rule "%(rule_name)s" cannot be processed (%(message)s)') % {
            'rule_name': exception.rule_name,
            'message': exception.message
        }
    elif isinstance(exception, lgr.exceptions.LGRApiInvalidParameter):
        message = _('Input parameter has invalid format')
    elif isinstance(exception, lgr.exceptions.LGRApiException):
        message = _('A general exception occurred in the LGR API')
    elif isinstance(exception, exceptions.LGRValidationException):
        message = _('LGR is not valid (%(args)s)') % {'args': exception.args[0]}
    elif isinstance(exception, exceptions.LGRInvalidLabelFileException):
        if exception.label:
            message = _('Label %(label)s is not valid in the LGR (%(message)s)') % {
                'label': exception.label,
                'message': exception.message
            }
        else:
            message = exception.message
    elif isinstance(exception, lgr.exceptions.InvalidSymmetry):
        message = _('The LGR contains a variant that do not have symmetric '
                    'relations')
    elif isinstance(exception, lgr.exceptions.LGRException):
        message = _('An unknown exception occurred in the LGR API')
    else:
        message = '%s' % exception

    return message
