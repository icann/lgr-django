# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView

from lgr_auth.models import LgrRole


class BaseAdminView(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.role == LgrRole.ADMIN.value


class BaseListAdminView(BaseAdminView, ListView):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'home_url_name': 'lgr_admin_mode'
        })
        return ctx
