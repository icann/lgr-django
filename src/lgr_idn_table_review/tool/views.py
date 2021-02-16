# -*- coding: utf-8 -*-
import uuid

from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

from lgr_advanced.lgr_editor.views import RE_SAFE_FILENAME
from lgr_idn_table_review.admin.models import RzLgr, RefLgr
from lgr_idn_table_review.tool.api import LgrIdnReviewSession
from lgr_idn_table_review.tool.forms import LGRIdnTableReviewForm, IdnTableReviewSelectReferenceForm
from lgr_idn_table_review.tool.tasks import idn_table_review_task
from lgr_web.views import INTERFACE_SESSION_KEY, Interfaces


class IdnTableReviewViewMixin:

    def dispatch(self, request, *args, **kwargs):
        self.session = LgrIdnReviewSession(request)
        return super().dispatch(request, *args, **kwargs)


class IdnTableReviewModeView(IdnTableReviewViewMixin, FormView):
    form_class = LGRIdnTableReviewForm
    template_name = 'lgr_idn_table_review_tool/review_mode.html'

    def get(self, request, *args, **kwargs):
        request.session[INTERFACE_SESSION_KEY] = Interfaces.IDN_REVIEW.name
        return super(IdnTableReviewModeView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('lgr_review_select_reference', kwargs={'report_id': self.report_id})

    def form_valid(self, form):
        self.report_id = str(uuid.uuid4())
        for idn_table in form.cleaned_data['idn_tables']:
            idn_table_id = idn_table.name
            if not RE_SAFE_FILENAME.match(idn_table_id):
                raise SuspiciousOperation()
            for ext in ['xml', 'txt']:
                if idn_table_id.endswith(f'.{ext}'):
                    idn_table_id = idn_table_id.rsplit('.', 1)[0]
                    break
            idn_table_id = slugify(idn_table_id)
            self.session.open_lgr(idn_table_id, idn_table.read().decode('utf-8'), uid=self.report_id)

        return super(IdnTableReviewModeView, self).form_valid(form)


class IdnTableReviewSelectReferenceView(IdnTableReviewViewMixin, FormView):
    form_class = IdnTableReviewSelectReferenceForm
    template_name = 'lgr_idn_table_review_tool/select_reference.html'
    success_url = reverse_lazy('lgr_review_report_folders')

    def form_valid(self, form):
        email_address = form.cleaned_data.pop('email', None)
        report_id = self.kwargs.get('report_id')

        idn_tables = []
        for idn_table, lgr_info in form.cleaned_data.items():
            idn_table_info = self.session.select_lgr(idn_table, uid=report_id)
            idn_tables.append((idn_table_info.to_dict(), lgr_info))

        if email_address:
            idn_table_review_task.delay(idn_tables, report_id, email_address, self.session.get_storage_path(),
                                        self.get_success_url(), self.request.build_absolute_uri())
        else:
            idn_table_review_task(idn_tables, report_id, None, self.session.get_storage_path(), self.get_success_url(),
                                  self.request.build_absolute_uri('/').rstrip('/'))

        return super(IdnTableReviewSelectReferenceView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(IdnTableReviewSelectReferenceView, self).get_form_kwargs()
        idn_tables = self.session.list_lgr(uid=self.kwargs.get('report_id'))
        kwargs['idn_tables'] = [t['name'] for t in idn_tables]
        kwargs['lgrs'] = {
            'rz': RzLgr.objects.order_by('name').values_list('name', flat=True),
            'ref': RefLgr.objects.order_by('name').values_list('name', flat=True)
        }

        return kwargs


class IdnTableReviewListReportFolders(IdnTableReviewViewMixin, TemplateView):
    template_name = 'lgr_idn_table_review_tool/list_report_folders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['folders'] = self.session.list_storage_folders()
        return context


class IdnTableReviewListReports(IdnTableReviewViewMixin, TemplateView):
    template_name = 'lgr_idn_table_review/list_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['storage'] = self.session.list_storage(subfolder=self.kwargs.get('folder'))
        zipname = f"{self.kwargs.get('folder')}.zip"
        if zipname in context['storage']:
            context['storage'].remove(zipname)
            context['zip'] = zipname
        context['completed'] = True  # FIXME: we don't know if this if finished or not
        context['title'] = _("IDN Table Review Reports: %(folder)s") % {'folder': self.kwargs.get('folder')}
        context['storage_type'] = 'rev_usr'
        context['back_url'] = 'lgr_review_report_folders'
        return context


class IdnTableReviewDisplayIdnTable(IdnTableReviewViewMixin, View):

    def get(self, request, *args, **kwargs):
        idn_table_info = self.session.select_lgr(self.kwargs.get('lgr_id'), uid=self.kwargs.get('report_id'))
        # FIXME: should distinct txt and xml LGRs
        resp = HttpResponse(idn_table_info.data, content_type='text/plain', charset='UTF-8')
        resp['Content-disposition'] = 'attachment'
        return resp
