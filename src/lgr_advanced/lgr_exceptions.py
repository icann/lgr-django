# -*- coding: utf-8 -*-
"""
lgr_exceptions.py - Map LGR exception to user terms.
"""
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

import lgr.exceptions
from lgr.utils import format_cp
from picu.exceptions import IDNAException
from lgr_models.exceptions import LGRValidationException, LGRUnsupportedUnicodeVersionException


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
        message = _('Code point %(codepoint)s has invalid context rule %(rule)s') % {
            'codepoint': format_cp(exception.cp),
            'rule': exception.rule or ''
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
        if reason == lgr.exceptions.LGRFormatException.LGRFormatReason.SEQUENCE_NO_TAG:
            message = _('Sequence cannot have a tag')
        elif reason == lgr.exceptions.LGRFormatException.LGRFormatReason.INVALID_LANGUAGE_TAG:
            message = _('Invalid language')
        elif reason == lgr.exceptions.LGRFormatException.LGRFormatReason.INVALID_DATE_TAG:
            message = _('Invalid date value')
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
    elif isinstance(exception, lgr.exceptions.ReferenceInvalidId):
        message = _('Invalid reference id %(ref_id)s ') % {
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
    elif isinstance(exception, LGRValidationException):
        message = _('LGR is not valid (%(args)s)') % {'args': exception.args[0]}
    elif isinstance(exception, LGRUnsupportedUnicodeVersionException):
        message = _('Unicode version (%(args)s) is not supported by the system') % {'args': exception.args[0]}
    elif isinstance(exception, lgr.exceptions.LGRInvalidLabelException):
        message = _('Label %(label)s is not valid in the LGR (%(message)s)') % {
            'label': exception.label,
            'message': exception.message
        }
    elif isinstance(exception, lgr.exceptions.LGRLabelCollisionException):
        message = _('Input label file contains collision(s)')
    elif isinstance(exception, lgr.exceptions.InvalidSymmetry):
        message = _('The LGR contains a variant that do not have symmetric '
                    'relations')
    elif isinstance(exception, lgr.exceptions.MissingLanguage):
        message = _('The LGR does not contain a valid language (%(message)s)' % {'message': exception.message})
    elif isinstance(exception, lgr.exceptions.LGRCrossScriptMissingDataException):
        message = _('Cannot generate cross-script variant for LGR without (%(message)s)' % {
            'message': exception.missing_part
        })
    elif isinstance(exception, lgr.exceptions.LGRException):
        message = _('An unknown exception occurred in the LGR API')
    elif isinstance(exception, IDNAException):
        messages = []
        for error in exception.error_labels:
            if error == 'UIDNA_ERROR_EMPTY_LABEL':
                messages.append(ugettext('Label is empty'))
            elif error == 'UIDNA_ERROR_LABEL_TOO_LONG':
                messages.append(ugettext('%(label)s is invalid due to its length being longer than 63 bytes.') % {
                    'label': exception.obj
                })
            # elif error == 'UIDNA_ERROR_DOMAIN_NAME_TOO_LONG':
            elif error == 'UIDNA_ERROR_LEADING_HYPHEN':
                messages.append(ugettext('%(label)s is invalid due to hyphen restrictions in the RFC5891 as it starts '
                                         'with a hyphen-minus.' % {
                                             'label': exception.obj
                                         }))
            elif error == 'UIDNA_ERROR_TRAILING_HYPHEN':
                messages.append(ugettext('%(label)s is invalid due to hyphen restrictions in the RFC5891 as it ends '
                                         'with a hyphen-minus.' % {
                                             'label': exception.obj
                                         }))
            elif error == 'UIDNA_ERROR_HYPHEN_3_4':
                messages.append(ugettext('%(label)s is invalid due to hyphen restrictions in the RFC5891 as it '
                                         'contains hyphen-minus in the third and fourth positions.' % {
                                             'label': exception.obj
                                         }))
            elif error == 'UIDNA_ERROR_LEADING_COMBINING_MARK':
                messages.append(ugettext('%(label)s is invalid due to leading combining marks restriction in the '
                                         'RFC5891.' % {
                                             'label': exception.obj
                                         }))
            elif error == 'UIDNA_ERROR_DISALLOWED':
                messages.append(ugettext('%(label)s is invalid as it contains disallowed characters.' % {
                    'label': exception.obj
                }))
            elif error == 'UIDNA_ERROR_PUNYCODE':
                messages.append(ugettext('%(label)s is invalid as it starts with ‘xn--’ but does not contain valid '
                                         'Punycode.' % {
                                             'label': exception.obj
                                         }))
            elif error == 'UIDNA_ERROR_LABEL_HAS_DOT':
                messages.append(ugettext('%(label)s is invalid as it contains full stop (dot).' % {
                    'label': exception.obj
                }))
            elif error == 'UIDNA_ERROR_INVALID_ACE_LABEL':
                messages.append(ugettext('%(label)s is invalid due to invalid Punycode.' % {'label': exception.obj}))
            elif error == 'UIDNA_ERROR_BIDI':
                messages.append(ugettext('%(label)s is invalid due to  the Bidi rule in the RFC5893.' % {
                    'label': exception.obj
                }))
            elif error == 'UIDNA_ERROR_CONTEXTJ':
                messages.append(ugettext('%(label)s is invalid due to the IDNA contextual rule for Zero Width '
                                         'Joiner.' % {
                                             'label': exception.obj
                                         }))
            elif error == 'UIDNA_ERROR_CONTEXTO_PUNCTUATION':
                messages.append(ugettext('%(label)s is invalid due to the IDNA contextual rule for punctuation in '
                                         'the RFC5892.' % {
                                             'label': exception.obj
                                         }))
            elif error == 'UIDNA_ERROR_CONTEXTO_DIGITS':
                messages.append(ugettext('%(label)s is invalid due to the IDNA contextual rule for digits in the '
                                         'RFC5892.' % {
                                             'label': exception.obj
                                         }))
            else:
                messages.append(exception)
            message = '\n'.join(messages)
    else:
        message = '%s' % exception

    return message
