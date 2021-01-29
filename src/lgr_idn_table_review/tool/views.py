# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import SuspiciousOperation
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import FormView

from lgr_advanced.lgr_editor.views import RE_SAFE_FILENAME
from lgr_idn_table_review.tool.api import session_open_idn_table, session_list_idn_tables, session_delete_idn_tables
from lgr_idn_table_review.tool.forms import LGRIdnTableReviewForm, IdnTableReviewSelectReferenceForm
from lgr_web.views import INTERFACE_SESSION_KEY, Interfaces


class IdnTableReviewModeView(FormView):
    form_class = LGRIdnTableReviewForm
    template_name = 'lgr_idn_table_review_tool/review_mode.html'
    success_url = reverse_lazy('lgr_review_select_reference')

    def get(self, request, *args, **kwargs):
        request.session[INTERFACE_SESSION_KEY] = Interfaces.REVIEW.name
        session_delete_idn_tables(request)
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
            session_open_idn_table(self.request, idn_table_id, str(idn_table.read()))

        return super(IdnTableReviewModeView, self).form_valid(form)


class IdnTableReviewSelectReferenceView(FormView):
    form_class = IdnTableReviewSelectReferenceForm
    template_name = 'lgr_idn_table_review_tool/select_reference.html'

    def form_valid(self, form):
        return super(IdnTableReviewSelectReferenceView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(IdnTableReviewSelectReferenceView, self).get_form_kwargs()
        idn_tables = session_list_idn_tables(self.request)
        kwargs['idn_tables'] = [t['name'] for t in idn_tables]
        kwargs['ref_lgrs'] = []
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(IdnTableReviewSelectReferenceView, self).get_context_data(**kwargs)
        return ctx
