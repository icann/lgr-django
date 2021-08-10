# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from lgr_auth.models import LgrRole
from lgr_idn_table_review.icann_tools.api import LGRIcannSession
from lgr_session.views import StorageType
from lgr_web.views import INTERFACE_SESSION_MODE_KEY, Interfaces
from .tasks import idn_table_review_task


class BaseIcannView(LoginRequiredMixin, UserPassesTestMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        request.session[INTERFACE_SESSION_MODE_KEY] = Interfaces.IDN_ICANN.name
        self.session = LGRIcannSession(request)

    def test_func(self):
        return self.request.user.role in [LgrRole.ICANN.value, LgrRole.ADMIN.value]


class IdnTableIcannModeView(BaseIcannView, TemplateView):
    template_name = 'lgr_idn_table_review_icann/icann_mode.html'

    def post(self, request, *args, **kwargs):
        idn_table_review_task.delay(self.request.build_absolute_uri('/').rstrip('/'),
                                    self.request.user.email)

        messages.info(request, _('Generating report. You will receive an email upon completion.'))
        return redirect('lgr_idn_icann_mode')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['folders'] = self.session.list_storage_folders()
        return context


class IdnTableIcannListReports(BaseIcannView, TemplateView):
    template_name = 'lgr_idn_table_review/list_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['storage'] = self.session.list_storage(subfolder=self.kwargs.get('folder'), reverse=False)
        zipname = f"{self.kwargs.get('folder')}.zip"
        if zipname in context['storage']:
            context['storage'].remove(zipname)
            context['zip'] = zipname
        summary_name = f"{self.kwargs.get('folder')}-summary.html"
        context['completed'] = False
        if summary_name in context['storage']:
            context['completed'] = True
        context['title'] = _("ICANN Review Reports: %(folder)s") % {'folder': self.kwargs.get('folder')}
        context['storage_type'] = StorageType.IDN_REVIEW_ICANN_MODE.value
        context['back_url'] = 'lgr_idn_icann_mode'
        return context
