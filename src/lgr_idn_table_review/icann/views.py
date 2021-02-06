# -*- coding: utf-8 -*-
import time
from io import BytesIO
from zipfile import ZipFile, ZIP_BZIP2

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from lgr.tools.idn_review.review import review_lgr
from lgr_auth.models import LgrRole
from lgr_idn_table_review.icann.api import LgrIcannSession, get_icann_idn_repository_tables, get_reference_lgr
from lgr_idn_table_review.tool.api import IdnTableInfo
from lgr_web.views import INTERFACE_SESSION_KEY, Interfaces


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
        zip_content = BytesIO()
        with ZipFile(zip_content, mode='w', compression=ZIP_BZIP2) as zf:
            for idn_table_info in get_icann_idn_repository_tables():
                context = self._review(idn_table_info)
                if context:
                    html_report = render_to_string('lgr_idn_table_review_tool/review.html', context)
                else:
                    context = {'name': idn_table_info.name}
                    html_report = render_to_string('lgr_idn_table_review_icann/not_reviewed.html', context)
                zf.writestr(f'{idn_table_info.name}.html', html_report)

        self.session.storage_save_file(f"{time.strftime('%Y%m%d_%H%M%S')}_idn_report.zip", zip_content)

        messages.info(request, _('Generating report. You will receive an email upon completion.'))
        return redirect('lgr_idn_icann_mode')

    def _review(self, idn_table_info):
        ref_lgr = get_reference_lgr(idn_table_info)
        if not ref_lgr:
            return None
        ref_lgr_info = IdnTableInfo.from_dict({
            'name': ref_lgr.name,
            'data': ref_lgr.file.read().decode('utf-8'),
        })
        return review_lgr(idn_table_info.lgr, ref_lgr_info.lgr)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['storage'] = self.session.list_storage()
        return context
