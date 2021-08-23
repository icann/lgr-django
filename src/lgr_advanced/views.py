# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView

from lgr.utils import cp_to_ulabel, format_cp
from lgr_advanced import unidb
from lgr_advanced.api import LGRToolStorage
from lgr_advanced.forms import LabelFormsForm
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.models import LgrModel
from lgr_advanced.utils import list_built_in_lgr
from lgr_web.views import Interfaces, INTERFACE_SESSION_MODE_KEY


class LGRViewMixin(LoginRequiredMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.storage = LGRToolStorage(request.user)
        request.session[INTERFACE_SESSION_MODE_KEY] = Interfaces.ADVANCED.name


class AdvancedModeView(LGRViewMixin, TemplateView):
    template_name = 'lgr_advanced/index.html'

    def get_context_data(self, **kwargs):
        ctx = super(AdvancedModeView, self).get_context_data(**kwargs)
        xml_files = list_built_in_lgr()
        ctx.update({
            'lgr_xml': xml_files,
            'lgrs': LgrModel.objects.filter(owner=self.request.user).all(),
            'reports': self.storage.list_storage(),
        })
        return ctx


class LabelFormsView(LoginRequiredMixin, FormView):
    form_class = LabelFormsForm
    template_name = 'lgr_advanced/label_forms.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = ''
        self.udata = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['unicode_versions'] = ((v, v) for v in settings.SUPPORTED_UNICODE_VERSIONS)
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.label:
            try:
                ctx['cp_list'] = format_cp(self.label)
                ctx['u_label'] = cp_to_ulabel(self.label)
                ctx['a_label'] = self.udata.idna_encode_label(ctx['u_label'])
            except UnicodeError as ex:
                messages.add_message(self.request, messages.ERROR,
                                     lgr_exception_to_text(ex))
        return ctx

    def form_valid(self, form):
        self.label = form.cleaned_data['label']
        unicode_version = form.cleaned_data['unicode_version']
        self.udata = unidb.manager.get_db_by_version(unicode_version)

        return self.render_to_response(self.get_context_data(form=form))
