# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.views.generic import TemplateView

from lgr.utils import cp_to_ulabel, format_cp
from lgr_advanced import unidb
from lgr_advanced.api import LgrToolSession
from lgr_advanced.forms import LabelFormsForm
from lgr_advanced.utils import list_built_in_lgr
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_web.views import Interfaces, INTERFACE_SESSION_KEY


class LgrViewMixin:

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.session = LgrToolSession(request)

    def get(self, request, *args, **kwargs):
        request.session[INTERFACE_SESSION_KEY] = Interfaces.ADVANCED.name
        return super().get(request, *args, **kwargs)


class AdvancedModeView(LgrViewMixin, TemplateView):
    template_name = 'lgr_advanced/index.html'

    def get_context_data(self, **kwargs):
        ctx = super(AdvancedModeView, self).get_context_data(**kwargs)
        xml_files = list_built_in_lgr()
        ctx.update({
            'lgr_xml': xml_files,
            'lgrs': self.session.list_lgr(),
            'lgr_id': '',
            'storage': self.session.list_storage(),
        })
        return ctx


class LabelFormsView(TemplateView):
    template_name = 'lgr_advanced/label_forms.html'

    def get_context_data(self, **kwargs):
        ctx = super(LabelFormsView, self).get_context_data(**kwargs)
        unicode_versions = ((v, v) for v in settings.SUPPORTED_UNICODE_VERSIONS)
        form = LabelFormsForm(self.request.POST or None,
                              unicode_versions=unicode_versions)
        if form.is_bound and form.is_valid():
            label = form.cleaned_data['label']
            unicode_version = form.cleaned_data['unicode_version']
            udata = unidb.manager.get_db_by_version(unicode_version)
            try:
                ctx['cp_list'] = format_cp(label)
                ctx['u_label'] = cp_to_ulabel(label)
                ctx['a_label'] = udata.idna_encode_label(ctx['u_label'])
            except UnicodeError as ex:
                messages.add_message(self.request, messages.ERROR,
                                     lgr_exception_to_text(ex))

        ctx['form'] = form
        return ctx
