# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DeleteView

from lgr_auth.models import LgrRole


class BaseAdminMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.role == LgrRole.ADMIN.value


class BaseAdminViewMixin(BaseAdminMixin):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'home_url_name': 'lgr_admin_mode'
        })
        return ctx


def initial_active(model, set_active=False):
    active = model.objects.filter(active=True).first()
    if active:
        return active.pk

    first = model.objects.first()
    if not first:
        return None
    if set_active:
        first.active = True
        first.save(update_fields=['active'])
    return first.pk


class BaseListAdminView(BaseAdminMixin, ListView):
    active_form = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['home_url_name'] = 'lgr_admin_mode'
        if self.active_form:
            ctx['active_choice_form'] = self.active_form(initial={'active': initial_active(self.model)})
        return ctx


class BaseCreateInitActiveMixin(BaseAdminMixin):
    active_form = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_list'] = self.model._default_manager.all()
        if self.active_form:
            ctx['active_choice_form'] = self.active_form(initial={'active': initial_active(self.model)})
        return ctx


class BaseDeleteModelInitActiveMixin(BaseAdminMixin, DeleteView):

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if self.object.active:
            initial_active(self.model, set_active=True)
        return response
