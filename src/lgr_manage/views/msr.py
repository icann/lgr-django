# -*- coding: utf-8 -*-
from django import views
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import SingleObjectMixin

from lgr_manage.forms import MSRCreateForm, MSRIsActiveForm
from lgr_manage.views.AjaxFormMixin import AjaxFormMixin
from lgr_manage.views.common import BaseListAdminView, BaseAdminView
from lgr_models.models.lgr import MSR


class MSRListView(BaseListAdminView):
    model = MSR
    template_name = 'lgr_manage/msr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MSRCreateForm()
        context['active_choice_form'] = MSRIsActiveForm(
            initial={'active': MSR.objects.filter(active=True).first().pk if MSR.objects.filter(
                active=True).exists() else 1})
        return context


class MSRCreateView(BaseAdminView, views.generic.CreateView):
    model = MSR
    form_class = MSRCreateForm
    template_name = 'lgr_manage/msr.html'
    success_url = reverse_lazy('lgr_admin_msr')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = MSRListView.model._default_manager.all()
        return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New MSR created'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to create MSR'))
        return super().form_invalid(form)


class MSRView(BaseAdminView, views.View):

    def get(self, request, *args, **kwargs):
        view = MSRListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = MSRCreateView.as_view()
        return view(request, *args, **kwargs)


class MSRDeleteView(BaseAdminView, views.generic.DeleteView):
    model = MSR
    success_url = reverse_lazy('lgr_admin_msr')
    pk_url_kwarg = 'lgr_pk'


class MSRIsActiveView(AjaxFormMixin, views.generic.edit.FormView):
    model = MSR
    form_class = MSRIsActiveForm
    template_name = 'lgr_manage/msr.html'
    success_url = reverse_lazy('lgr_admin_msr')


class DisplayMSRView(SingleObjectMixin, views.View):
    pk_url_kwarg = 'lgr_pk'
    model = MSR

    def get(self, request, *args, **kwargs):
        lgr = self.get_object()
        return HttpResponse(lgr.file.read(), content_type='text/xml', charset='UTF-8')
