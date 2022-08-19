# -*- coding: utf-8 -*-
from django import views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import SingleObjectMixin

from lgr_manage.forms import RefLgrCreateForm, RefLgrIsActiveForm
from lgr_manage.views.ajax_mixin import AjaxFormViewMixin
from lgr_manage.views.common import BaseListAdminView, BaseAdminMixin
from lgr_models.models.lgr import RefLgr


class RefLgrListView(BaseListAdminView):
    model = RefLgr
    template_name = 'lgr_manage/ref_lgr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = RefLgrCreateForm()
        context['active_choice_form'] = RefLgrIsActiveForm(
            initial={'active': self.initial_active()})
        return context

    def initial_active(self):
        active = RefLgr.objects.filter(active=True).first()
        if active:
            return active.pk

        return 1


class RefLgrCreateView(BaseAdminMixin, views.generic.CreateView):
    model = RefLgr
    form_class = RefLgrCreateForm
    template_name = 'lgr_manage/ref_lgr.html'
    success_url = reverse_lazy('lgr_admin_ref_lgr')

    def get_success_url(self):
        return reverse_lazy('lgr_admin_ref_lgr')
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['object_list'] = RefLgrListView.model._default_manager.all()
    #     return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New Reference LGR created'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to create Reference LGR'))
        return super().form_invalid(form)


class RefLgrView(BaseAdminMixin, views.View):

    def get(self, request, *args, **kwargs):
        view = RefLgrListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = RefLgrCreateView.as_view()
        return view(request, *args, **kwargs)


class RefLgrDeleteView(BaseAdminMixin, views.generic.DeleteView):
    model = RefLgr
    success_url = reverse_lazy('lgr_admin_ref_lgr')
    pk_url_kwarg = 'lgr_pk'


class RefLgrIsActiveView(AjaxFormViewMixin, views.generic.edit.FormView):
    model = RefLgr
    form_class = RefLgrIsActiveForm
    template_name = 'lgr_manage/ref_lgr.html'
    success_url = reverse_lazy('lgr_admin_ref_lgr')
