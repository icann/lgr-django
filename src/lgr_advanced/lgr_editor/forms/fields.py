# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_editor.utils import list_validating_repertoires
from lgr_advanced.utils import list_root_zones

UNICODE_VERSIONS = tuple((v, v) for v in settings.SUPPORTED_UNICODE_VERSIONS)
DEFAULT_UNICODE_VERSION = settings.SUPPORTED_UNICODE_VERSIONS[0]

VALIDATING_REPERTOIRES = tuple((v, v) for v in list_validating_repertoires())
DEFAULT_VALIDATING_REPERTOIRE = ''

FILE_FIELD_ENCODING_HELP = _('File must be encoded in UTF-8 and using 0x0A line ending.')
