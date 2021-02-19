#! /bin/env python
# -*- coding: utf-8 -*-
"""
validate - 
"""
import logging

from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.views import View

from lgr_advanced import unidb
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin

logger = logging.getLogger(__name__)


class ValidateLGRView(LGRHandlingBaseMixin, View):
    """
    Validate an LGR and display result.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.output_func = self.kwargs.get('output_func')

    def get(self, request, *args, **kwargs):
        # Construct options dictionary for checks/validations
        options = {}
        try:
            options['unidb'] = unidb.manager.get_db_by_version(self.lgr_info.lgr.metadata.unicode_version)
        except KeyError:
            pass
        if self.lgr_info.validating_repertoire is not None:
            options['validating_repertoire'] = self.lgr_info.validating_repertoire
        options['rng_filepath'] = settings.LGR_RNG_FILE

        results = self.lgr_info.lgr.validate(options)
        tpl_name = 'lgr_editor/validate_lgr.html'

        # XXX hack to get translation in validation descriptions and process them automatically by makemessages
        _("Testing XML validity using RNG"),
        _("Testing symmetry"),
        _("Testing transitivity"),
        _("Testing conditional variants"),
        _("Generate stats"),
        _("Rebuilding LGR")
        for r in results:
            r[1]['description'] = _(r[1]['description'])
        # end hack

        context = {
            'results': results,
            'name': self.lgr_id
        }
        if self.output_func:
            return self.output_func(self.lgr_id, render_to_string(tpl_name, context))
        else:
            return render(request, tpl_name, context)
