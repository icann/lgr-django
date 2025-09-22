import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _, ngettext
from django.views import View
from django.views.generic import FormView, TemplateView

from lgr_advanced.lgr_editor.views.create import RE_SAFE_FILENAME
from lgr_idn_table_review.idn_tool.api import LGRIdnReviewApi
from lgr_idn_table_review.idn_tool.forms import IdnTableReviewSelectReferenceForm, LGRIdnTableReviewForm
from lgr_idn_table_review.idn_tool.tasks import idn_table_review_task
from lgr_tasks.models import LgrTaskModel
from lgr_utils.views import safe_next_redirect_url

logger = logging.getLogger(__name__)


class IdnTableReviewViewMixin(LoginRequiredMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.api = LGRIdnReviewApi(request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'home_url_name': 'lgr_review_mode'
        })
        return ctx


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
                lgr = self.api.create_lgr(idn_table_file,
                                          idn_table_name,
                                          self.report_id)
                # check LGR can be parsed
                lgr.to_lgr()
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
        idn_tables = []
        for idn_table_pk, lgr_info in form.cleaned_data.items():
            if isinstance(lgr_info, InMemoryUploadedFile):
                lgr_info = self.api.create_reflgr(file=File(lgr_info),
                                                  name=lgr_info.name.split(".")[0],
                                                  report_id=self.report_id).to_tuple()
            idn_tables.append((idn_table_pk, str(lgr_info)))

        task = LgrTaskModel.objects.create(app=self.request.resolver_match.app_name,
                                           name=ngettext('Review of %(count)d IDN table',
                                                         'Review of %(count)d IDN tables',
                                                         len(idn_tables)) % {'count': len(idn_tables)},
                                           user=self.request.user)
        idn_table_review_task.apply_async((self.request.user.pk, idn_tables, self.report_id,
                                           self.request.build_absolute_uri('/').rstrip('/')),
                                          task_id=task.pk)

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
        context['display_exp'] = True
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


class IdnTableReviewDeleteReport(IdnTableReviewViewMixin, View):

    def post(self, request, *args, **kwargs):
        self.api.delete_report(self.kwargs.get('report_id'))
        return redirect(safe_next_redirect_url(request, '/'))
