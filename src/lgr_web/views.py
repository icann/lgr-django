# -*- coding: utf-8 -*-
from enum import Enum, auto

from dal import autocomplete
from django.conf import settings
from django.views.generic import TemplateView

from lgr_web.utils import IANA_LANG_REGISTRY


class Interfaces(Enum):
    ADVANCED = auto()
    BASIC = auto()
    IDN_REVIEW = auto()
    IDN_ICANN = auto()
    IDN_ADMIN = auto()


class LGRModesView(TemplateView):
    template_name = 'lgr_modes.html'


class LGRAboutView(TemplateView):
    """
    About dialog
    """
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['output'] = settings.SUPPORTED_UNICODE_VERSION
        return ctx


class LGRHelpView(TemplateView):
    """
    Help dialog
    """
    template_name = 'help.html'


class LanguageAutocomplete(autocomplete.Select2ListView):

    def get_list(self):
        return sorted(IANA_LANG_REGISTRY)

    def create(self, value):
        return value
