# -*- coding: utf-8 -*-
import time
from ast import literal_eval
from io import BytesIO
from zipfile import ZipFile

from django.core.exceptions import SuspiciousOperation, ValidationError
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, TemplateView

from lgr.tools.idn_review.review import review_lgr
from lgr_advanced.api import LGRInfo
from lgr_advanced.lgr_editor.views import RE_SAFE_FILENAME
from lgr_idn_table_review.admin.models import RzLgr, RefLgr, LgrModel
from lgr_idn_table_review.tool.api import LgrIdnReviewSession
from lgr_idn_table_review.tool.forms import LGRIdnTableReviewForm, IdnTableReviewSelectReferenceForm
from lgr_web.views import INTERFACE_SESSION_KEY, Interfaces


class IdnTableReviewViewMixin:

    def dispatch(self, request, *args, **kwargs):
        self.session = LgrIdnReviewSession(request)
        return super().dispatch(request, *args, **kwargs)


class IdnTableReviewModeView(FormView, IdnTableReviewViewMixin):
    form_class = LGRIdnTableReviewForm
    template_name = 'lgr_idn_table_review_tool/review_mode.html'
    success_url = reverse_lazy('lgr_review_select_reference')

    def get(self, request, *args, **kwargs):
        request.session[INTERFACE_SESSION_KEY] = Interfaces.IDN_REVIEW.name
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


class IdnTableReviewSelectReferenceView(FormView, IdnTableReviewViewMixin):
    form_class = IdnTableReviewSelectReferenceForm
    template_name = 'lgr_idn_table_review_tool/select_reference.html'
    success_url = reverse_lazy('lgr_review_reports')

    def form_valid(self, form):
        idn_review_contexts = {}
        email_address = form.cleaned_data.pop('email', None)
        for idn_table, lgr_info in form.cleaned_data.items():
            idn_table_info = self.session.select_lgr(idn_table)
            idn_table_as_lgr = LGRInfo.from_dict(
                {
                    'name': idn_table_info.name,
                    'xml': idn_table_info.data,
                    'validate': False,
                }, None)
            lgr_type, lgr_name = literal_eval(lgr_info)
            try:
                if lgr_type == 'ref':
                    ref_lgr = RefLgr.objects.get(name=lgr_name)
                elif lgr_type == 'rz':
                    ref_lgr = RzLgr.objects.get(name=lgr_name)
                else:
                    raise ValidationError(_('Unable to retrieve reference LGR'))
            except LgrModel.DoesNotExist:
                raise ValidationError(_('Unable to retrieve reference LGR'))
            ref_lgr_info = LGRInfo.from_dict(
                {
                    'name': ref_lgr.name,
                    'xml': ref_lgr.file.read(),
                    'validate': False,
                }, None)

            idn_review_contexts[idn_table_as_lgr.name] = review_lgr(idn_table_as_lgr.lgr, ref_lgr_info.lgr)

        zip_content = BytesIO()
        with ZipFile(zip_content, mode='w') as zf:
            for name, context in idn_review_contexts.items():
                html_report = render_to_string('lgr_idn_table_review_tool/review.html', context)
                zf.writestr(f'{name}.html', html_report)

        self.session.storage_save_file(f"{time.strftime('%Y%m%d_%H%M%S')}_idn_table_review.zip", zip_content)

        if email_address:
            # TODO put process in queue and send email once finished
            pass

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
