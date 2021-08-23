# -*- coding: utf-8 -*-
"""
views.py - Views for the LGR renderer.
"""
from __future__ import unicode_literals
from django.views.generic import TemplateView

from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin
from lgr_advanced.lgr_renderer.api import generate_context


class LGRRendererView(LGRHandlingBaseMixin, TemplateView):
    template_name = 'lgr_renderer.html'

    def get_context_data(self, **kwargs):
        context = super(LGRRendererView, self).get_context_data(**kwargs)
        context.update(generate_context(self.lgr))
        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Render the template as an attachment if required.
        """
        html_response = super(LGRRendererView, self).render_to_response(context, **response_kwargs)
        if 'save' in self.request.GET:
            html_response['Content-Disposition'] = f'attachment; filename="{self.lgr.name}.html"'
        return html_response
