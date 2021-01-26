# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
from django.conf import settings
from lgr_advanced.lgr_editor.utils import list_validating_repertoires, list_root_zones, parse_language_registry

UNICODE_VERSIONS = tuple((v, v) for v in settings.SUPPORTED_UNICODE_VERSIONS)
DEFAULT_UNICODE_VERSION = settings.SUPPORTED_UNICODE_VERSIONS[0]

VALIDATING_REPERTOIRES = tuple((v, v) for v in list_validating_repertoires())
DEFAULT_VALIDATING_REPERTOIRE = ''

ROOT_ZONES = tuple((v, re.sub(r'lgr-([1-9]+)-.*', r'RZ-LGR version \1', v)) for v in sorted(list_root_zones()))

IANA_LANG_REGISTRY = parse_language_registry()
