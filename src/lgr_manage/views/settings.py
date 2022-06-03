# -*- coding: utf-8 -*-
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from lgr_manage.forms import LgrSettingsForm
from lgr_manage.views.common import BaseAdminViewMixin
from lgr_models.models.settings import LGRSettings


class LgrSettingsView(BaseAdminViewMixin, UpdateView):
    template_name = 'lgr_manage/settings.html'
    form_class = LgrSettingsForm
    model = LGRSettings
    success_url = reverse_lazy('lgr_admin_settings')

    def get_object(self, queryset=None):
        return self.model._default_manager.get(pk=1)
