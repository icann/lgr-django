# -*- coding: utf-8 -*-

from django.core.exceptions import SuspiciousOperation
from django.urls import reverse_lazy
from django.utils.text import slugify
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
    success_url = reverse_lazy('lgr_review_select_reference')

    def get(self, request, *args, **kwargs):
        request.session[INTERFACE_SESSION_KEY] = Interfaces.IDN_REVIEW.name
        # remove IDN files from session, we restart an new IDN review process
        self.session.delete_all()
        return super(IdnTableReviewModeView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        for idn_table in form.cleaned_data['idn_tables']:
            idn_table_id = idn_table.name
            if not RE_SAFE_FILENAME.match(idn_table_id):
                raise SuspiciousOperation()
            for ext in ['xml', 'txt']:
                if idn_table_id.endswith(f'.{ext}'):
                    idn_table_id = idn_table_id.rsplit('.', 1)[0]
                    break
            idn_table_id = slugify(idn_table_id)
            self.session.open_lgr(idn_table_id, idn_table.read().decode('utf-8'))

        return super(IdnTableReviewModeView, self).form_valid(form)


class IdnTableReviewSelectReferenceView(IdnTableReviewViewMixin, FormView):
    form_class = IdnTableReviewSelectReferenceForm
    template_name = 'lgr_idn_table_review_tool/select_reference.html'
    success_url = reverse_lazy('lgr_review_reports')

    def form_valid(self, form):
        email_address = form.cleaned_data.pop('email', None)

        idn_tables = []
        for idn_table, lgr_info in form.cleaned_data.items():
            idn_table_info = self.session.select_lgr(idn_table)
            idn_tables.append((idn_table_info.to_dict(), lgr_info))

        if email_address:
            idn_table_review_task.delay(idn_tables, self.request.user.email, self.session.get_storage_path(),
                                        self.success_url)
        else:
            idn_table_review_task(idn_tables, self.request.user.email, self.session.get_storage_path(),
                                  self.success_url)

        return super(IdnTableReviewSelectReferenceView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(IdnTableReviewSelectReferenceView, self).get_form_kwargs()
        idn_tables = self.session.list_lgr()
        kwargs['idn_tables'] = [t['name'] for t in idn_tables]
        kwargs['lgrs'] = {
            'rz': RzLgr.objects.order_by('name').values_list('name', flat=True),
            'ref': RefLgr.objects.order_by('name').values_list('name', flat=True)
        }

        return kwargs


class IdnTableReviewListReports(IdnTableReviewViewMixin, TemplateView):
    template_name = 'lgr_idn_table_review_tool/list_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['storage'] = self.session.list_storage()
        return context
