import logging

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views import View

from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin
from lgr_utils import unidb

logger = logging.getLogger(__name__)


class ValidateLGRView(LGRHandlingBaseMixin, View):
    """
    Validate an LGR and display result.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.output = self.kwargs.get('output', False)

    def get(self, request, *args, **kwargs):
        # Construct options dictionary for checks/validations
        options = {}
        try:
            options['unidb'] = unidb.manager.get_db_by_version(self.lgr.metadata.unicode_version)
        except KeyError:
            pass
        if self.lgr_object.validating_repertoire:
            options['validating_repertoire'] = self.lgr_object.validating_repertoire.to_lgr(
                with_unidb=False, expand_ranges=True)
        options['rng_filepath'] = settings.LGR_RNG_FILE

        results = self.lgr.validate(options)
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
            'name': self.lgr_object.name
        }

        if self.output:
            response = HttpResponse(content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="{self.lgr_object.name}-validation-results.html"'
            response.write(render_to_string(tpl_name, context))
            return response
        else:
            return render(request, tpl_name, context)
