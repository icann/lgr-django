# -*- coding: utf-8 -*-
from django import views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import SingleObjectMixin

from lgr_manage.forms import IDNACreateForm, IDNAIsActiveForm
from lgr_manage.views.ajax_mixin import AjaxFormViewMixin
from lgr_manage.views.common import BaseListAdminView, BaseAdminMixin
from lgr_models.models.lgr import IDNARepertoire


class IDNAListView(BaseListAdminView):
    model = IDNARepertoire
    template_name = 'lgr_manage/idna.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = IDNACreateForm()
        context['active_choice_form'] = IDNAIsActiveForm(
            initial={'active': self.initial_active()})
        return context

    def initial_active(self):
        active = IDNARepertoire.objects.filter(active=True).first()
        if active:
            return active.pk

        return 1


class IDNACreateView(BaseAdminMixin, views.generic.CreateView):
    model = IDNARepertoire
    form_class = IDNACreateForm
    template_name = 'lgr_manage/idna.html'
    success_url = reverse_lazy('lgr_admin_idna')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = IDNAListView.model._default_manager.all()
        return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New IDNA Reportoire created'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to create IDNA Repertoire'))
        return super().form_invalid(form)


class IDNAView(BaseAdminMixin, views.View):

    def get(self, request, *args, **kwargs):
        view = IDNAListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = IDNACreateView.as_view()
        return view(request, *args, **kwargs)


class IDNADeleteView(BaseAdminMixin, views.generic.DeleteView):
    model = IDNARepertoire
    success_url = reverse_lazy('lgr_admin_idna')
    pk_url_kwarg = 'lgr_pk'


class IDNAIsActiveView(AjaxFormViewMixin, views.generic.edit.FormView):
    model = IDNARepertoire
    form_class = IDNAIsActiveForm
    template_name = 'lgr_manage/idna.html'
    success_url = reverse_lazy('lgr_admin_idna')
