# -*- coding: utf-8 -*-
import logging

from dal_select2.views import Select2GroupListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView
from django.views.generic.detail import SingleObjectMixin

from lgr_advanced.lgr_editor.views.create import RE_SAFE_FILENAME
from lgr_idn_table_review.idn_tool.api import LGRIdnReviewApi
from lgr_idn_table_review.idn_tool.forms import LGRIdnTableReviewForm, IdnTableReviewSelectReferenceForm
from lgr_idn_table_review.idn_tool.tasks import idn_table_review_task
from lgr_models.models.lgr import RzLgr, RefLgr, RzLgrMember
from lgr_web.views import INTERFACE_SESSION_MODE_KEY, Interfaces

logger = logging.getLogger(__name__)


class IdnTableReviewViewMixin(LoginRequiredMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.api = LGRIdnReviewApi(request.user)
        request.session[INTERFACE_SESSION_MODE_KEY] = Interfaces.IDN_REVIEW.name


class IdnTableReviewModeView(IdnTableReviewViewMixin, FormView):
    form_class = LGRIdnTableReviewForm
    template_name = 'lgr_idn_table_review_tool/review_mode.html'

    def get_success_url(self):
        return reverse('lgr_review_select_reference', kwargs={'report_id': self.report_id})

    def form_valid(self, form):
        self.report_id = self.api.generate_report_id()
        for idn_table_file in self.request.FILES.getlist('idn_tables'):
            idn_table_name = idn_table_file.name
            if not RE_SAFE_FILENAME.match(idn_table_name):
                raise SuspiciousOperation()
            for ext in ['xml', 'txt']:
                if idn_table_name.endswith(f'.{ext}'):
                    idn_table_name = idn_table_name.rsplit('.', 1)[0]
                    break
            try:
                self.api.create_lgr(idn_table_file,
                                    idn_table_name,
                                    self.report_id)
            except Exception:
                logger.exception('Unable to parser IDN table %s', idn_table_name)
                form.add_error('idn_tables', _('%(filename)s is an invalid IDN table') % {'filename': idn_table_name})
                return super().form_invalid(form)

        return super(IdnTableReviewModeView, self).form_valid(form)


class IdnTableReviewSelectReferenceView(IdnTableReviewViewMixin, FormView):
    form_class = IdnTableReviewSelectReferenceForm
    template_name = 'lgr_idn_table_review_tool/select_reference.html'
    success_url = reverse_lazy('lgr_review_reports')

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.report_id = self.kwargs.get('report_id')

    def form_valid(self, form):
        email_address = self.request.user.email

        idn_tables = []
        for idn_table_pk, lgr_info in form.cleaned_data.items():
            idn_tables.append((idn_table_pk, lgr_info))

        idn_table_review_task.delay(idn_tables, self.report_id, email_address,
                                    self.request.build_absolute_uri(self.get_success_url()),
                                    self.request.build_absolute_uri('/').rstrip('/'))

        return super(IdnTableReviewSelectReferenceView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(IdnTableReviewSelectReferenceView, self).get_form_kwargs()
        kwargs['idn_tables'] = self.api.get_lgrs_in_report(self.report_id)
        return kwargs


class IdnTableReviewListReports(IdnTableReviewViewMixin, TemplateView):
    template_name = 'lgr_idn_table_review_tool/list_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = self.api.list_storage()
        return context


class IdnTableReviewListReport(IdnTableReviewViewMixin, TemplateView):
    template_name = 'lgr_idn_table_review/list_report_files.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zipname = f"{self.kwargs.get('report_id')}.zip"
        context['reports'] = self.api.list_storage(report_id=self.kwargs.get('report_id'),
                                                   exclude={'file__endswith': zipname})
        context['completed'] = True
        try:
            context['zip'] = self.api.storage_find_report_file(self.kwargs.get('report_id'), zipname)
        except self.api.storage_model.DoesNotExist:
            context['completed'] = False
        context['title'] = _("IDN Table Review Reports: %(report)s") % {'report': self.kwargs.get('report_id')}
        context['back_url'] = 'lgr_review_reports'
        return context


class IdnTableReviewDisplayIdnTable(IdnTableReviewViewMixin, SingleObjectMixin, View):
    pk_url_kwarg = 'lgr_pk'
    model = LGRIdnReviewApi.lgr_model

    def get(self, request, *args, **kwargs):
        idn_table = self.get_object(queryset=self.api.lgr_queryset())
        # FIXME: should distinct txt and xml LGRs
        content_type = 'text/plain'
        if idn_table.filename.endswith('xml'):
            content_type = 'text/xml'
        resp = HttpResponse(idn_table.file.read(), content_type=content_type, charset='UTF-8')
        resp['Content-disposition'] = f'attachment; filename={idn_table.filename}'
        return resp


class IdnTableReviewDeleteReport(IdnTableReviewViewMixin, View):

    def post(self, request, *args, **kwargs):
        self.api.delete_report(self.kwargs.get('report_id'))
        return redirect(request.GET.get('next', '/'))


class RefLgrAutocomplete(LoginRequiredMixin, Select2GroupListView):

    @staticmethod
    def get_list():
        lgr_choices = []
        for rz in RzLgr.objects.all():
            rz_member_choices = ((str(rz.to_tuple()), rz.name),) + tuple(
                (str(rz_member.to_tuple()), rz_member.name) for rz_member in RzLgrMember.objects.filter(rz_lgr=rz))
            lgr_choices += [((rz.name, rz.name), rz_member_choices)]
        lgr_choices += [(('Ref. LGR', 'Ref. LGR'), tuple(
            ((str(ref_lgr.to_tuple()), ref_lgr.name) for ref_lgr in RefLgr.objects.all())))]
        return lgr_choices
