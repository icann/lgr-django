# -*- coding: utf-8 -*-
"""
views.py - Views for the LGR renderer.
"""
from __future__ import unicode_literals

from django.http import Http404, HttpResponse
from django.views.generic import TemplateView

from lgr_advanced.lgr_renderer.api import generate_context
from lgr_advanced.views import LGRViewMixin
from lgr_models.models import RzLgr


class LGRRendererView(LGRViewMixin, TemplateView):
    template_name = 'lgr_renderer.html'

    def get(self, request, *args, **kwargs):
        self.lgr_info = self.session.select_lgr(kwargs['lgr_id'], kwargs.get('lgr_set_id'))
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


class LGRRendererDbView(LGRRendererView):
    def get(self, request, *args, **kwargs):
        if kwargs['format'] not in ['xml', 'html']:
            raise Http404

        self.lgr_info = RzLgr.objects.get(pk=kwargs['lgr_pk']).to_lgr_info()
        if kwargs['format'] == 'html':
            return super(LGRRendererView, self).get(request, *args, **kwargs)

        return HttpResponse(self.lgr_info.xml, content_type='text/xml', charset='UTF-8')
