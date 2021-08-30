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

        if not self.lgr_object.is_set():
            return HttpResponseBadRequest('LGR is not a set')

        ctx.update({
            'embedded': self.lgr_object.embedded_lgrs(),
        })
        return ctx
