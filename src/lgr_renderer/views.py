# -*- coding: utf-8 -*-
"""
views.py - Views for the LGR renderer.
"""
from django import views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView

from lgr_renderer.api import generate_context


class LGRRendererView(LoginRequiredMixin, TemplateView):
    template_name = 'lgr_renderer.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        lgr_pk = self.kwargs['lgr_pk']
        lgr_model = self.kwargs['model']
        lgr_object = lgr_model.get_object(request.user, lgr_pk)
        self.lgr = lgr_object.to_lgr()

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


class LGRDisplayView(LoginRequiredMixin, views.View):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        lgr_pk = self.kwargs['lgr_pk']
        lgr_model = self.kwargs['model']
        self.force_download = self.kwargs.get('force_download', False)
        self.lgr_object = lgr_model.get_object(request.user, lgr_pk)

    def get(self, request, *args, **kwargs):
        content_type = 'text/plain'
        if self.lgr_object.filename.endswith('xml'):
            content_type = 'text/xml'
        resp = HttpResponse(self.lgr_object.file, content_type=content_type, charset='UTF-8')
        if self.force_download:
            resp['Content-disposition'] = f'attachment; filename={self.lgr_object.filename}'
        return resp
