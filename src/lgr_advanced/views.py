# -*- coding: utf-8 -*-
from django.views.generic import TemplateView

from lgr_advanced.lgr_editor.api import session_list_lgr, session_list_storage
from lgr_advanced.lgr_editor.utils import list_built_in_lgr
from lgr_web.views import Interfaces, INTERFACE_SESSION_KEY


class AdvancedModeView(TemplateView):
    template_name = 'lgr_advanced/index.html'

    def get(self, request, *args, **kwargs):
        request.session[INTERFACE_SESSION_KEY] = Interfaces.ADVANCED.name
        return super(AdvancedModeView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(AdvancedModeView, self).get_context_data(**kwargs)
        xml_files = list_built_in_lgr()
        ctx.update({
            'lgr_xml': xml_files,
            'lgrs': session_list_lgr(self.request),
            'lgr_id': '',
            'storage': session_list_storage(self.request),
        })
        return ctx
