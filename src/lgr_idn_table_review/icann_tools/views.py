# -*- coding: utf-8 -*-
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from lgr_idn_table_review.icann_tools.api import LGRIcannStorage
from lgr_tasks.models import LgrTaskModel
from .tasks import idn_table_review_task


class BaseIcannView(LoginRequiredMixin, UserPassesTestMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.storage = LGRIcannStorage(request.user)

    def test_func(self):
        return self.request.user.is_icann()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'home_url_name': 'lgr_idn_icann_mode'
        })
        return ctx


class IdnTableIcannModeView(BaseIcannView, TemplateView):
    template_name = 'lgr_idn_table_review_icann/icann_mode.html'

    def post(self, request, *args, **kwargs):
        task = LgrTaskModel.objects.create(app=self.request.resolver_match.app_name,
                                           name=_('ICANN IDN Tables Review'),
                                           user=self.request.user)
        idn_table_review_task.apply_async((self.request.user.pk,
                                           self.request.build_absolute_uri('/').rstrip('/')),
                                          task_id=task.pk)

        messages.info(request,
                      mark_safe(_('Generating report. You can follow your task progression in the %s.') % (
                          f"<a href='{reverse('list_process')}'>{_('task status page')}</a>")))
        return redirect('lgr_idn_icann_mode')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = self.storage.list_storage()
        return context


class IdnTableIcannListReports(BaseIcannView, TemplateView):
    template_name = 'lgr_idn_table_review/list_report_files.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zipname = f"{self.kwargs.get('report_id')}.zip"
        summary_name = f"{self.kwargs.get('report_id')}-summary.html"
        exclude_filter = [{'file__endswith': zipname},
                          {'file__endswith': summary_name}]
        if settings.DEBUG:
            exclude_filter.append({'file__endswith': '.json'})
        context['reports'] = self.storage.list_storage(report_id=self.kwargs.get('report_id'), reverse=False,
                                                       exclude=exclude_filter)
        context['completed'] = True
        try:
            context['zip'] = self.storage.storage_find_report_file(self.kwargs.get('report_id'), zipname)
            context['summary'] = self.storage.storage_find_report_file(self.kwargs.get('report_id'), summary_name)
        except self.storage.storage_model.DoesNotExist:
            messages.warning(self.request,
                             _('Task is still being processed, please come back later for the full report.'))
            context['completed'] = False
        context['title'] = _("ICANN Review Reports: %(report)s") % {'report': self.kwargs.get('report_id')}
        context['back_url'] = 'lgr_idn_icann_mode'
        return context
