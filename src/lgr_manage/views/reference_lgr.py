# -*- coding: utf-8 -*-
from django import views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from lgr_manage.forms import RefLgrCreateForm, RefLgrMemberUpdateForm, RefLgrIsActiveForm
from lgr_manage.views.ajax_mixin import AjaxFormViewMixin
from lgr_manage.views.common import (BaseListAdminView,
                                     BaseAdminMixin,
                                     BaseDeleteModelInitActiveMixin,
                                     BaseCreateInitActiveMixin,
                                     initial_active)
from lgr_models.models.lgr import RefLgr, RefLgrMember


class RefLgrListView(BaseListAdminView):
    model = RefLgr
    template_name = 'lgr_manage/ref_lgr.html'
    active_form = RefLgrIsActiveForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = RefLgrCreateForm()
        return context


class RefLgrCreateView(BaseCreateInitActiveMixin, views.generic.CreateView):
    model = RefLgr
    form_class = RefLgrCreateForm
    template_name = 'lgr_manage/ref_lgr.html'
    success_url = reverse_lazy('lgr_admin_ref_lgr')
    active_form = RefLgrIsActiveForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New Reference LGR created'))
        response = super().form_valid(form)
        initial_active(RefLgr, set_active=True)
        return response

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


class RefLgrDeleteView(BaseDeleteModelInitActiveMixin):
    model = RefLgr
    success_url = reverse_lazy('lgr_admin_ref_lgr')
    pk_url_kwarg = 'lgr_pk'


class RefLgrIsActiveView(AjaxFormViewMixin, views.generic.edit.FormView):
    model = RefLgr
    form_class = RefLgrIsActiveForm
    template_name = 'lgr_manage/ref_lgr.html'
    success_url = reverse_lazy('lgr_admin_ref_lgr')


class RefLgrMemberUpdateView(BaseAdminMixin, views.generic.UpdateView):
    model = RefLgrMember
    form_class = RefLgrMemberUpdateForm
    template_name = 'lgr_manage/ref_lgr_member.html'
    pk_url_kwarg = 'lgr_pk'

    def get_success_url(self):
        return reverse_lazy('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = RefLgrListView.model._default_manager.all()
        context['active_choice_form'] = RefLgrIsActiveForm(initial={'active': initial_active(RefLgr)})
        return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('Reference LGR member updated'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to update Reference LGR member'))
        return super().form_invalid(form)
