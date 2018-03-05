# -*- coding: utf-8 -*-
"""
views.py - Views for the LGR renderer.
"""
from __future__ import unicode_literals
from django.views.generic import TemplateView

from lgr_editor.api import session_select_lgr
from lgr_renderer.api import generate_context


class LGRRendererView(TemplateView):
    template_name = 'lgr_renderer.html'

    def get(self, request, *args, **kwargs):
        self.lgr_info = session_select_lgr(request, kwargs['lgr_id'], kwargs['lgr_set_id'])
        return super(LGRRendererView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LGRRendererView, self).get_context_data(**kwargs)
        context.update(generate_context(self.lgr_info.lgr))
        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Render the template as an attachment if required.
        """
        html_response = super(LGRRendererView, self).render_to_response(context, **response_kwargs)
        if 'save' in self.request.GET:
            html_response['Content-Disposition'] = 'attachment; filename="{}.html"'.format(self.lgr_info.lgr)
        return html_response