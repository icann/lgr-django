# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.http import (HttpResponseBadRequest)
from django.views.generic import TemplateView

from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin

logger = logging.getLogger(__name__)


class EmbeddedLGRsView(LGRHandlingBaseMixin, TemplateView):
    template_name = 'lgr_editor/embedded_lgrs.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if not self.lgr_info.is_set:
            return HttpResponseBadRequest('LGR is not a set')

        ctx.update({
            'lgr': self.lgr_info.lgr,
            'lgr_id': self.lgr_id,
            'embedded': self.lgr_info.lgr_set,
            'is_set': True
        })
        return ctx
