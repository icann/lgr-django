# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from lgr_editor.utils import list_validating_repertoires


UNICODE_VERSIONS = tuple((v, v) for v in settings.SUPPORTED_UNICODE_VERSIONS)
DEFAULT_UNICODE_VERSION = settings.SUPPORTED_UNICODE_VERSIONS[0]

VALIDATING_REPERTOIRES = tuple((v, v) for v in list_validating_repertoires())
DEFAULT_VALIDATING_REPERTOIRE = ''
