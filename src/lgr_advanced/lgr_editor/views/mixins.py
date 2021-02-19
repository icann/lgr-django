#! /bin/env python
# -*- coding: utf-8 -*-
"""
mixins - 
"""
import logging

from lgr_advanced.views import LgrViewMixin

logger = logging.getLogger(__name__)


class LGRHandlingBaseMixin(LgrViewMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lgr_id = None
        self.lgr_set_id = None
        self.lgr_info = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_id = self.kwargs['lgr_id']
        self.lgr_set_id = self.kwargs.get('lgr_set_id')
        self.lgr_info = self.session.select_lgr(self.lgr_id, self.lgr_set_id)