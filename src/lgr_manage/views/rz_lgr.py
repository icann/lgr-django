# -*- coding: utf-8 -*-
from django import views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import SingleObjectMixin

from lgr_manage.forms import RzLgrCreateForm, RzLgrIsActiveForm
from lgr_manage.views.ajax_mixin import AjaxFormViewMixin
from lgr_manage.views.common import BaseListAdminView, BaseAdminMixin
from lgr_models.models.lgr import RzLgr


class RzLgrListView(BaseListAdminView):
    model = RzLgr
    template_name = 'lgr_manage/rz_lgr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = RzLgrCreateForm()
        context['active_choice_form'] = RzLgrIsActiveForm(
            initial={'active': self.initial_active()})

        return context

    def initial_active(self):
        active = RzLgr.objects.filter(active=True).first()
        if active:
            return active.pk

        return 1


class RzLgrCreateView(BaseAdminMixin, views.generic.CreateView):
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


class RzLgrView(BaseAdminMixin, views.View):

    def get(self, request, *args, **kwargs):
        view = RzLgrListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = RzLgrCreateView.as_view()
        return view(request, *args, **kwargs)


class RzLgrDeleteView(BaseAdminMixin, views.generic.DeleteView):
    model = RzLgr
    success_url = reverse_lazy('lgr_admin_rz_lgr')
    pk_url_kwarg = 'lgr_pk'


class RzLgrIsActiveView(AjaxFormViewMixin, views.generic.edit.FormView):
    model = RzLgr
    form_class = RzLgrIsActiveForm
    template_name = 'lgr_manage/rz_lgr.html'
    success_url = reverse_lazy('lgr_admin_rz_lgr')
