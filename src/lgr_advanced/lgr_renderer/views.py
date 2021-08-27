# -*- coding: utf-8 -*-
"""
views.py - Views for the LGR renderer.
"""
from __future__ import unicode_literals

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from lgr_advanced.lgr_renderer.api import generate_context


class LGRRendererView(LoginRequiredMixin, TemplateView):
    template_name = 'lgr_renderer.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        lgr_pk = self.kwargs['lgr_pk']
        lgr_model = self.kwargs['model']
        query_kwargs = {'pk': lgr_pk}
        if not lgr_model._meta.get_field('owner').null:
            # only include owner in model where it is mandatory, meaning objects are private
            query_kwargs['owner'] = request.user
        lgr_object = lgr_model.objects.get(**query_kwargs)
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
