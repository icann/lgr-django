# -*- coding: utf-8 -*-

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from lgr_advanced.api import LGRToolReportStorage
from lgr_advanced.models import LgrModel
from lgr_advanced.utils import list_built_in_lgr
from lgr_models.models.lgr import RzLgr


class LGRViewMixin(LoginRequiredMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.storage = LGRToolReportStorage(request.user)

    def get_context_data(self, **kwargs):
        ctx = super(LGRViewMixin, self).get_context_data(**kwargs)
        ctx.update({
            'home_url_name': 'lgr_advanced_mode'
        })
        return ctx


class AdvancedModeView(LGRViewMixin, TemplateView):
    template_name = 'lgr_advanced/index.html'

    def get_context_data(self, **kwargs):
        ctx = super(AdvancedModeView, self).get_context_data(**kwargs)
        current_lgrs = set(LgrModel.objects.filter(owner=self.request.user).values_list('name', flat=True))
        xml_files = [l for l in list_built_in_lgr() if l not in current_lgrs]
        ctx.update({
            'built_in_lgr_files': xml_files,
            'built_in_lgrs': RzLgr.objects.exclude(name__in=current_lgrs),
            'lgrs': LgrModel.objects.filter(owner=self.request.user).all(),
            'reports': self.storage.list_storage(),
        })
        return ctx
