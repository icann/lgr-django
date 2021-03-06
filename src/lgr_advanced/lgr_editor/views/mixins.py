#! /bin/env python
# -*- coding: utf-8 -*-
"""
mixins - 
"""
import logging

from django.http import HttpResponseBadRequest

from lgr_advanced.views import LGRViewMixin

logger = logging.getLogger(__name__)


class LGRHandlingBaseMixin(LGRViewMixin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lgr_id = None
        self.lgr_set_id = None
        self.lgr_info = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_id = self.kwargs['lgr_id']
        self.lgr_set_id = self.kwargs.get('lgr_set_id')
        self.lgr_info = self.session.select_lgr(self.lgr_id, self.lgr_set_id)


class LGREditMixin(LGRHandlingBaseMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.lgr_info.is_set:
            return HttpResponseBadRequest('Cannot edit LGR set')
