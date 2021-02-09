# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from lgr_auth.models import LgrRole
from lgr_idn_table_review.icann.api import LgrIcannSession
from lgr_web.views import INTERFACE_SESSION_KEY, Interfaces
from .tasks import idn_table_review_task


class IdnTableIcannModeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'lgr_idn_table_review_icann/icann_mode.html'

    def dispatch(self, request, *args, **kwargs):
        self.session = LgrIcannSession(request)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.role in [LgrRole.ICANN.value, LgrRole.ADMIN.value]

    def get(self, request, *args, **kwargs):
        request.session[INTERFACE_SESSION_KEY] = Interfaces.IDN_ICANN.name
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        idn_table_review_task.delay(email_address=self.request.user.email)

        messages.info(request, _('Generating report. You will receive an email upon completion.'))
        return redirect('lgr_idn_icann_mode')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['storage'] = self.session.list_storage()
        return context
