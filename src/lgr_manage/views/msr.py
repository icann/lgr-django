from django import views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from lgr_manage.forms import MSRCreateForm, MSRIsActiveForm
from lgr_manage.views.ajax_mixin import AjaxFormViewMixin
from lgr_manage.views.common import (
    BaseAdminMixin,
    BaseCreateInitActiveMixin,
    BaseDeleteModelInitActiveMixin,
    BaseListAdminView,
    initial_active)
from lgr_models.models.lgr import MSR


class MSRListView(BaseListAdminView):
    model = MSR
    template_name = 'lgr_manage/msr.html'
    active_form = MSRIsActiveForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MSRCreateForm()
        return context


class MSRCreateView(BaseCreateInitActiveMixin, views.generic.CreateView):
    model = MSR
    form_class = MSRCreateForm
    template_name = 'lgr_manage/msr.html'
    success_url = reverse_lazy('lgr_admin_msr')
    active_form = MSRIsActiveForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New MSR created'))
        response = super().form_valid(form)
        initial_active(MSR, set_active=True)
        return response

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to create MSR'))
        return super().form_invalid(form)


class MSRView(BaseAdminMixin, views.View):

    def get(self, request, *args, **kwargs):
        view = MSRListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = MSRCreateView.as_view()
        return view(request, *args, **kwargs)


class MSRDeleteView(BaseDeleteModelInitActiveMixin):
    model = MSR
    success_url = reverse_lazy('lgr_admin_msr')
    pk_url_kwarg = 'lgr_pk'


class MSRIsActiveView(AjaxFormViewMixin, views.generic.edit.FormView):
    model = MSR
    form_class = MSRIsActiveForm
    template_name = 'lgr_manage/msr.html'
    success_url = reverse_lazy('lgr_admin_msr')
