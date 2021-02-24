# -*- coding: utf-8 -*-
from django import views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from lgr_auth.models import LgrRole
from lgr_web.views import INTERFACE_SESSION_MODE_KEY, Interfaces


class BaseAdminView(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.role == LgrRole.ADMIN.value


class BaseListAdminView(BaseAdminView, views.generic.ListView):

    def setup(self, request, *args, **kwargs):
        request.session[INTERFACE_SESSION_MODE_KEY] = Interfaces.IDN_ADMIN.name
        return super().setup(request, *args, **kwargs)
