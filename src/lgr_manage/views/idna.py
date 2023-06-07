# -*- coding: utf-8 -*-
from django import views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from lgr_manage.forms import IDNACreateForm, IDNAIsActiveForm
from lgr_manage.views.ajax_mixin import AjaxFormViewMixin
from lgr_manage.views.common import BaseListAdminView, BaseAdminMixin, BaseCreateInitActiveMixin, \
    BaseDeleteModelInitActiveMixin, initial_active
from lgr_models.models.lgr import IDNARepertoire


class IDNAListView(BaseListAdminView):
    model = IDNARepertoire
    template_name = 'lgr_manage/idna.html'
    active_form = IDNAIsActiveForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = IDNACreateForm()
        return context


class IDNACreateView(BaseCreateInitActiveMixin, views.generic.CreateView):
    model = IDNARepertoire
    form_class = IDNACreateForm
    template_name = 'lgr_manage/idna.html'
    success_url = reverse_lazy('lgr_admin_idna')
    active_form = IDNAIsActiveForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New IDNA Repertoire created'))
        response = super().form_valid(form)
        initial_active(IDNARepertoire, set_active=True)
        return response


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


class IDNADeleteView(BaseDeleteModelInitActiveMixin):
    model = IDNARepertoire
    success_url = reverse_lazy('lgr_admin_idna')
    pk_url_kwarg = 'lgr_pk'


class IDNAIsActiveView(AjaxFormViewMixin, views.generic.edit.FormView):
    model = IDNARepertoire
    form_class = IDNAIsActiveForm
    template_name = 'lgr_manage/idna.html'
    success_url = reverse_lazy('lgr_admin_idna')
