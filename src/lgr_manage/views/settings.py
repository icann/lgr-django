# -*- coding: utf-8 -*-
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView, RedirectView

from lgr_manage.forms import LgrSettingsForm
from lgr_manage.views.common import BaseAdminViewMixin
from lgr_models.models.settings import LGRSettings
from lgr_tasks.api import is_task_completed
from lgr_tasks.models import LgrTaskModel
from lgr_tasks.tasks import calculate_index_variant_labels_tlds

TASK_NAME = 'Calculate the index variant labels of the existing TLDs'


class LgrSettingsView(BaseAdminViewMixin, UpdateView):
    template_name = 'lgr_manage/settings.html'
    form_class = LgrSettingsForm
    model = LGRSettings
    success_url = reverse_lazy('lgr_admin_settings')

    def get_object(self, queryset=None):
        return self.model._default_manager.get(pk=1)


class LgrCalculateIndexes(BaseAdminViewMixin, RedirectView):
    url = reverse_lazy('lgr_admin_settings')

    def post(self, request, *args, **kwargs):
        calculate_index_tasks = LgrTaskModel.objects.filter(name=TASK_NAME).last()
        if not calculate_index_tasks or is_task_completed(calculate_index_tasks.pk):
            messages.info(self.request,
                          _('The calculation of the index variant of the existing TLDs has been triggered'))
            task = LgrTaskModel.objects.create(app=self.request.resolver_match.app_name,
                                               name=TASK_NAME,
                                               user=self.request.user)
            calculate_index_variant_labels_tlds.apply_async((), task_id=task.pk)
        else:
            messages.warning(self.request, _('The index variant calculation has already been triggered, please wait'))

        return super().post(request, *args, **kwargs)
