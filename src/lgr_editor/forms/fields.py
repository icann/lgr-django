# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
from django.conf import settings
from lgr_editor.utils import list_validating_repertoires, list_root_zones


UNICODE_VERSIONS = tuple((v, v) for v in settings.SUPPORTED_UNICODE_VERSIONS)
DEFAULT_UNICODE_VERSION = settings.SUPPORTED_UNICODE_VERSIONS[0]

VALIDATING_REPERTOIRES = tuple((v, v) for v in list_validating_repertoires())
DEFAULT_VALIDATING_REPERTOIRE = ''

ROOT_ZONES = tuple((v, re.sub(r'lgr-([1-9]+)-.*', 'RZ-LGR version \1', v)) for v in list_root_zones())
