#! /bin/env python
# -*- coding: utf-8 -*-
"""
codepoints - 
"""
import logging

from django.http import HttpResponseBadRequest

from lgr_advanced.lgr_editor.utils import slug_to_cp
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin

logger = logging.getLogger(__name__)


class CodePointMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.codepoint_id = None
        self.codepoint = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.codepoint_id = self.kwargs['codepoint_id']
        self.codepoint = slug_to_cp(self.codepoint_id)


class LGREditMixin(LGRHandlingBaseMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.lgr_info.is_set:
            return HttpResponseBadRequest('Cannot edit LGR set')
