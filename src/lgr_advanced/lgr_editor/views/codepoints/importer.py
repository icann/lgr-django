#! /bin/env python
# -*- coding: utf-8 -*-
"""
importer.py -
"""
import logging
from io import StringIO

from django.contrib import messages
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from lgr.core import LGR
from lgr.exceptions import LGRException
from lgr.parser.line_parser import LineParser
from lgr.parser.rfc3743_parser import RFC3743Parser
from lgr.parser.rfc4290_parser import RFC4290Parser
from lgr_advanced.api import copy_characters
from lgr_advanced.lgr_editor.forms import (AddMultiCodepointsForm,
                                           AddRangeForm,
                                           ImportCodepointsFromFileForm,
                                           AddCodepointFromScriptForm)
from lgr_advanced.lgr_editor.utils import slug_to_cp
from lgr_advanced.lgr_editor.views.mixins import LGREditMixin
from lgr_advanced.models import LgrModel, TmpLgrModel
from lgr_models.models.lgr import LgrBaseModel
from lgr_utils import unidb
from lgr_utils.cp import cp_to_slug

logger = logging.getLogger(__name__)

INPUT_FILE_PARSER = {
    'rfc3743': RFC3743Parser,
    'rfc4290': RFC4290Parser,
    'one_per_line': LineParser
}


class MultiCodepointsView(LGREditMixin, FormView):
    """
    Basic view to handle some kind of input which generates a list of
    codepoints.

    It first presents the `form_class` to get inputs from user.
    Then, it renders the `AddMultiCodepointsForm` with the choices.
    """
    template_name = 'lgr_editor/add_list.html'
    success_template_name = 'lgr_editor/add_list_success.html'

    def __init__(self, discrete_cp=False):
        super(MultiCodepointsView, self).__init__()
        self.unidata = None
        self.discrete_cp = discrete_cp

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.unidata = unidb.manager.get_db_by_version(self.lgr.metadata.unicode_version)

    def post(self, request, *args, **kwargs):
        tmp_lgr_object = None
        if 'tmp_lgr' in request.POST:
            tmp_lgr_pk = self.request.POST.get('tmp_lgr')
            if tmp_lgr_pk:
                try:
                    tmp_lgr_object = TmpLgrModel.objects.get(owner=request.user,
                                                             pk=tmp_lgr_pk)
                    tmp_lgr = tmp_lgr_object.to_lgr()
                except LgrModel.DoesNotExist:
                    logger.warning("Unable to find temporary LGR, won't be able to get variants")
        if 'codepoint' in request.POST:
            # assume that we are submitting the `AddMultiCodepointsForm`
            codepoints = [slug_to_cp(cp) for cp in self.request.POST.getlist('codepoint')]
            if self.discrete_cp:
                for cp in codepoints:
                    self.lgr.add_cp(cp)
                    # find variants in temporary LGR
                    if tmp_lgr:
                        for variant in tmp_lgr.get_variants(cp):
                            self.lgr.add_variant(cp, variant.cp, force=True)
            else:
                # slug_to_cp returns a list of tuples, add codepoints need a
                # list. There is not variant here so taking first element of the
                # tuple is correct
                codepoints = [x[0] for x in codepoints]
                self.lgr.add_codepoints(codepoints)
                # no variants in range
            self.update_lgr()
            messages.add_message(self.request,
                                 messages.SUCCESS,
                                 _("%d code points added") % len(codepoints))
            # remove temporary LGR
            if tmp_lgr_object:
                tmp_lgr_object.delete()
            return self.render_success_page()

        return super(MultiCodepointsView, self).post(request, *args, **kwargs)

    def render_success_page(self):
        return TemplateResponse(
            request=self.request,
            template=self.success_template_name,
            context={
                'url': reverse('codepoint_list',
                               kwargs={
                                   'lgr_pk': self.lgr_pk,
                                   'model': self.lgr_object.model_name
                               })
            },
            using=self.template_engine,
        )

    def format_cp_choice(self, cp):
        slug = cp_to_slug(cp)
        return (slug, format_html_join('', 'U+{} {}',
                                       (('{:04X}'.format(c), self.unidata.get_char_name(c)) for c in cp)))

    def _handle_discrete(self, lgr, input_lgr, manual):
        logger.debug("Import: Copy references")
        # No choice here, we have to import references
        for (ref_id, ref) in input_lgr.reference_manager.items():
            value = ref['value']
            comment = ref.get('comment', None)
            try:
                lgr.add_reference(value, comment, ref_id=ref_id)
            except LGRException:
                logger.warning("Cannot add reference: '%s'", ref_id)

        if manual:
            # Start by expanding all ranges in manual mode
            input_lgr.expand_ranges()
            # we now use `AddMultiCodepointsForm` to present the list of code points
            range_form = AddMultiCodepointsForm()

            # Do note that importing codepoints from a file in manual mode
            # will lose some data from the file:
            #  - No codepoint attributes (comments, references, etc.)
            codepoint = []
            disabled_codepoint = []
            for char in input_lgr.repertoire:
                try:
                    lgr.add_cp(char.cp,
                               comment=char.comment,
                               ref=char.references,
                               validating_repertoire=self.validating_repertoire)
                except LGRException:
                    disabled_codepoint.append(self.format_cp_choice(char.cp))
                else:
                    codepoint.append(self.format_cp_choice(char.cp))

            if not codepoint and not disabled_codepoint:
                messages.add_message(self.request,
                                     messages.ERROR,
                                     _("No code point in input file"))
                return self.render_to_response(self.get_context_data())

            # Save LGR in sessions in order to retrieve variants in post
            tmp_lgr_object = TmpLgrModel.new(self.request.user,
                                             input_lgr)

            range_form.fields['codepoint'].choices = codepoint
            range_form.fields['disabled_codepoint'].choices = disabled_codepoint
            range_form.fields['tmp_lgr'].initial = tmp_lgr_object.pk
            return self.render_to_response(self.get_context_data(form=range_form))

        # Automatic import
        logger.debug("Import: Copy characters")
        nb_codepoints = copy_characters(lgr, input_lgr, validating_repertoire=self.validating_repertoire)
        self.update_lgr()
        messages.add_message(self.request,
                             messages.SUCCESS,
                             _("%d code points added") % nb_codepoints)
        return self.render_success_page()


class AddRangeView(MultiCodepointsView):
    """
    This view uses the `AddRangeForm` form to accept the `first_cp` and
    `last_cp` inputs from user.
    """
    form_class = AddRangeForm
    template_name = 'lgr_editor/add_list_range.html'

    def form_valid(self, form):
        # we now use `AddMultiCodepointsForm` to present the list of code points
        self.template_name = 'lgr_editor/add_list.html'
        range_form = AddMultiCodepointsForm()
        cd = form.cleaned_data
        # populate the choices with code points of the view
        codepoint_status = self.lgr.check_range(cd['first_cp'],
                                                cd['last_cp'],
                                                validating_repertoire=self.validating_repertoire)

        codepoint = []
        disabled_codepoint = []
        for (cp, status) in codepoint_status:
            if status is None:
                codepoint.append(self.format_cp_choice((cp,)))
            elif isinstance(status, LGRException):
                disabled_codepoint.append(self.format_cp_choice((cp,)))
        range_form.fields['codepoint'].choices = codepoint
        range_form.fields['disabled_codepoint'].choices = disabled_codepoint
        return self.render_to_response(self.get_context_data(form=range_form))


class ImportCodepointsFromFileView(MultiCodepointsView):
    """
    This view uses the `ImportCodepointsFromFileForm` form to parse a file.
    """
    form_class = ImportCodepointsFromFileForm
    template_name = 'lgr_editor/add_list_import.html'

    def __init__(self):
        # Importing codepoint from file should insert discrete codepoints
        super(ImportCodepointsFromFileView, self).__init__(discrete_cp=True)

    def form_valid(self, form):
        self.template_name = 'lgr_editor/add_list.html'
        cd = form.cleaned_data

        logger.debug("Import CP from file")
        # Get the type of input file and send it to LGR Core
        # Assume encoded in UTF-8
        file = StringIO(cd['file'].read().decode('utf-8'))
        type = cd['type']

        parser_cls = INPUT_FILE_PARSER.get(type, None)
        if parser_cls is None:
            logger.error("Unknown type '%s'", type)
            # Re-render the context data with the data-filled form and errors.
            return self.render_to_response(self.get_context_data(form=form))

        parser = parser_cls(file, filename=cd['file'].name, force=True)
        input_lgr = parser.parse_document()
        return self._handle_discrete(self.lgr, input_lgr, cd['manual_import'])


class AddCodepointFromScriptView(MultiCodepointsView):
    """
    This view uses the `AddCodepointFromScriptForm` form to retrieve code points from script based on MSR or
    IDNA2008.
    """
    form_class = AddCodepointFromScriptForm
    template_name = 'lgr_editor/add_list_from_script.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['unicode_database'] = self.lgr.unicode_database
        return kwargs

    def form_valid(self, form):
        self.template_name = 'lgr_editor/add_list.html'

        cd = form.cleaned_data
        script = cd['script']
        validating_repertoire = LgrBaseModel.from_tuple(cd['validating_repertoire']).to_lgr(with_unidb=False,
                                                                                            expand_ranges=True)

        codepoints = []
        for char in validating_repertoire.repertoire.all_repertoire():
            # XXX: Assume validating repertoire only contains single CP
            cp = char.cp[0]
            if script == self.lgr.unicode_database.get_script(cp, alpha4=True):
                codepoints.append(cp)

        fake_lgr = LGR(name=script)
        fake_lgr.add_codepoints(set(codepoints))
        return self._handle_discrete(self.lgr, fake_lgr, cd['manual_import'])
