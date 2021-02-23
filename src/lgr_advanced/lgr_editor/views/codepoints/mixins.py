#! /bin/env python
# -*- coding: utf-8 -*-
"""
codepoints - 
"""
import logging

from lgr_advanced.lgr_editor.utils import slug_to_cp

logger = logging.getLogger(__name__)


class CodePointMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.codepoint_id = None
        self.codepoint = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.codepoint_id = self.kwargs['codepoint_id']
        self.codepoint = slug_to_cp(self.codepoint_id)
