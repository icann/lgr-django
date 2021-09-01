# -*- coding: utf-8 -*-
from django import views
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import SingleObjectMixin

from lgr_models.models.lgr import RzLgr, RzLgrMember
from lgr_manage.forms import RzLgrCreateForm
from lgr_manage.views.common import BaseListAdminView, BaseAdminView


class RzLgrListView(BaseListAdminView):
    model = RzLgr
    template_name = 'lgr_manage/rz_lgr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = RzLgrCreateForm()
        return context


class RzLgrCreateView(BaseAdminView, views.generic.CreateView):
    model = RzLgr
    form_class = RzLgrCreateForm
    template_name = 'lgr_manage/rz_lgr.html'
    success_url = reverse_lazy('lgr_admin_rz_lgr')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = RzLgrListView.model._default_manager.all()
        return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New RZ LGR created'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to create RZ LGR'))
        return super().form_invalid(form)


class RzLgrView(BaseAdminView, views.View):

    def get(self, request, *args, **kwargs):
        view = RzLgrListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = RzLgrCreateView.as_view()
        return view(request, *args, **kwargs)


class RzLgrDeleteView(BaseAdminView, views.generic.DeleteView):
    model = RzLgr
    success_url = reverse_lazy('lgr_admin_rz_lgr')
    pk_url_kwarg = 'lgr_id'


class DisplayRzLgrView(SingleObjectMixin, views.View):
    pk_url_kwarg = 'lgr_id'
    model = RzLgr

    def get(self, request, *args, **kwargs):
        lgr = self.get_object()
        return HttpResponse(lgr.file.read(), content_type='text/xml', charset='UTF-8')


class DisplayRzLgrMemberView(SingleObjectMixin, views.View):
    pk_url_kwarg = 'lgr_id'
    model = RzLgrMember

    def get(self, request, *args, **kwargs):
        lgr = self.get_object()
        return HttpResponse(lgr.file.read(), content_type='text/xml', charset='UTF-8')

    def get_queryset(self):
        return self.model.objects.filter(rz_lgr__pk=self.kwargs.get('rz_lgr_id'))
