# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_editor.utils import list_validating_repertoires
from lgr_business.unicode_versions import UnicodeVersions

UNICODE_VERSIONS = tuple((v.version, v.version) for v in UnicodeVersions().get())
DEFAULT_UNICODE_VERSION = UNICODE_VERSIONS[0]

VALIDATING_REPERTOIRES = tuple((v, v) for v in list_validating_repertoires())
DEFAULT_VALIDATING_REPERTOIRE = ''

FILE_FIELD_ENCODING_HELP = _('File must be encoded in UTF-8 and using 0x0A line ending.')
