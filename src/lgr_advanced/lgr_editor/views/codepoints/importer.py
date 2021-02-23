#! /bin/env python
# -*- coding: utf-8 -*-
"""
importer.py -
"""
import logging
from io import StringIO

from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.six import iteritems
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from lgr.char import RangeChar
from lgr.core import LGR
from lgr.exceptions import LGRException
from lgr.parser.line_parser import LineParser
from lgr.parser.rfc3743_parser import RFC3743Parser
from lgr.parser.rfc4290_parser import RFC4290Parser
from lgr.utils import format_cp
from lgr_advanced import unidb
from lgr_advanced.lgr_editor.forms import (AddMultiCodepointsForm,
                                           AddRangeForm,
                                           ImportCodepointsFromFileForm,
                                           AddCodepointFromScriptForm)
from lgr_advanced.lgr_editor.repertoires import get_all_scripts_from_repertoire, get_by_name
from lgr_advanced.lgr_editor.utils import slug_to_cp
from lgr_advanced.lgr_editor.views.mixins import LGREditMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.utils import (cp_to_slug)

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
        self.lgr_info = None
        self.unidata = None
        self.discrete_cp = discrete_cp

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.unidata = unidb.manager.get_db_by_version(self.lgr_info.lgr.metadata.unicode_version)

    def post(self, request, *args, **kwargs):
        tmp_lgr_info = None
        if 'tmp_lgr' in request.POST:
            tmp_lgr_name = self.request.POST.get('tmp_lgr')
            if tmp_lgr_name:
                for saved_lgr in self.session.list_lgr():
                    if tmp_lgr_name == saved_lgr['name']:
                        tmp_lgr_info = self.session.select_lgr(tmp_lgr_name)
                if not tmp_lgr_info:
                    logger.warning("Unable to find temporary LGR, won't be able to "
                                   "get variants")
                    self.session.delete_lgr(tmp_lgr_name)
        if 'codepoint' in request.POST:
            # assume that we are submitting the `AddMultiCodepointsForm`
            codepoints = [slug_to_cp(cp) for cp in self.request.POST.getlist('codepoint')]
            if self.discrete_cp:
                for cp in codepoints:
                    self.lgr_info.lgr.add_cp(cp)
                    # find variants in temporary LGR
                    if tmp_lgr_info:
                        for variant in tmp_lgr_info.lgr.get_variants(cp):
                            self.lgr_info.lgr.add_variant(cp, variant.cp)
            else:
                # slug_to_cp returns a list of tuples, add codepoints need a
                # list. There is not variant here so taking first element of the
                # tuple is correct
                codepoints = [x[0] for x in codepoints]
                self.lgr_info.lgr.add_codepoints(codepoints)
                # no variants in range
            self.session.save_lgr(self.lgr_info)
            messages.add_message(self.request,
                                 messages.SUCCESS,
                                 _("%d code points added") % len(codepoints))
            # remove temporary LGR
            if tmp_lgr_info:
                self.session.delete_lgr(tmp_lgr_info.name)
            return self.render_success_page()

        return super(MultiCodepointsView, self).post(request, *args, **kwargs)

    def render_success_page(self):
        return TemplateResponse(
            request=self.request,
            template=self.success_template_name,
            context={'url': reverse('codepoint_list', args=(self.kwargs['lgr_id'],))},
            using=self.template_engine,
        )

    def format_cp_choice(self, cp):
        slug = cp_to_slug(cp)
        return (slug, format_html_join('', 'U+{} {}',
                                       (('{:04X}'.format(c), self.unidata.get_char_name(c)) for c in cp)))

    def _handle_discrete(self, lgr, input_lgr, manual):
        logger.debug("Import: Copy references")
        # No choice here, we have to import references
        for (ref_id, ref) in iteritems(input_lgr.reference_manager):
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
                               validating_repertoire=self.lgr_info.validating_repertoire)
                except LGRException:
                    disabled_codepoint.append(self.format_cp_choice(char.cp))
                else:
                    codepoint.append(self.format_cp_choice(char.cp))

            if len(codepoint) == 0:
                messages.add_message(self.request,
                                     messages.ERROR,
                                     _("No code point in input file"))
                return self.render_to_response(self.get_context_data())

            # Save LGR in sessions in order to retrieve variants in post
            tmp_lgr_id = input_lgr.name
            tmp_lgr_id = tmp_lgr_id
            if tmp_lgr_id.endswith('.txt'):
                tmp_lgr_id = tmp_lgr_id.rsplit('.', 1)[0]
            tmp_lgr_id += '_tmp'
            tmp_lgr_id = slugify(tmp_lgr_id)
            if tmp_lgr_id in [saved_lgr['name'] for saved_lgr in self.session.list_lgr()]:
                # The temporary LGR already exists... This should not happen
                logger.warning("Temporary LGR already exists...")
            else:
                tmp_lgr_info = self.session.new_lgr(tmp_lgr_id,
                                                    lgr.metadata.unicode_version,
                                                    self.lgr_info.validating_repertoire.name if self.lgr_info.validating_repertoire else None)
                self._copy_characters(tmp_lgr_info.lgr, input_lgr, force=True)
                self.session.save_lgr(tmp_lgr_info)

            range_form.fields['codepoint'].choices = codepoint
            range_form.fields['disabled_codepoint'].choices = disabled_codepoint
            range_form.fields['tmp_lgr'].initial = tmp_lgr_id
            return self.render_to_response(self.get_context_data(form=range_form))

        # Automatic import
        logger.debug("Import: Copy characters")
        nb_codepoints = self._copy_characters(lgr, input_lgr)
        self.session.save_lgr(self.lgr_info)
        messages.add_message(self.request,
                             messages.SUCCESS,
                             _("%d code points added") % nb_codepoints)
        return self.render_success_page()

    def _copy_characters(self, lgr, input_lgr, force=False):
        nb_codepoints = 0
        for char in input_lgr.repertoire:
            char_len = 1
            add_fct = lambda c: lgr.add_cp(c.cp,
                                           comment=c.comment,
                                           ref=c.references,
                                           validating_repertoire=self.lgr_info.validating_repertoire,
                                           force=force)
            if isinstance(char, RangeChar):
                char_len = char.last_cp - char.first_cp + 1
                add_fct = lambda c: lgr.add_range(c.first_cp, c.last_cp,
                                                  comment=c.comment,
                                                  ref=c.references,
                                                  validating_repertoire=self.lgr_info.validating_repertoire,
                                                  force=force)
            try:
                add_fct(char)
                nb_codepoints += char_len
            except LGRException as exc:
                logger.warning("Cannot add code point '%s': %s",
                               format_cp(char.cp),
                               lgr_exception_to_text(exc))
            else:
                for variant in char.get_variants():
                    try:
                        lgr.add_variant(char.cp,
                                        variant.cp,
                                        variant_type=variant.type,
                                        when=variant.when,
                                        not_when=variant.not_when,
                                        comment=variant.comment,
                                        ref=variant.references,
                                        validating_repertoire=self.lgr_info.validating_repertoire,
                                        force=force)
                    except LGRException as exc:
                        logger.warning("Cannot add variant '%s' to "
                                       "code point '%s': %s",
                                       format_cp(variant.cp),
                                       format_cp(char.cp),
                                       lgr_exception_to_text(exc))
        return nb_codepoints


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
        codepoint_status = self.lgr_info.lgr.check_range(cd['first_cp'],
                                                         cd['last_cp'],
                                                         validating_repertoire=self.lgr_info.validating_repertoire)

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

        lgr = self.lgr_info.lgr
        parser = parser_cls(file, filename=cd['file'].name)
        input_lgr = parser.parse_document()
        return self._handle_discrete(lgr, input_lgr, cd['manual_import'])


class AddCodepointFromScriptView(MultiCodepointsView):
    """
    This view uses the `AddCodepointFromScriptForm` form to retrieve code points from script based on MSR or
    IDNA2008.
    """
    form_class = AddCodepointFromScriptForm
    template_name = 'lgr_editor/add_list_from_script.html'

    def get(self, request, *args, **kwargs):
        self.lgr_info = self.session.select_lgr(kwargs['lgr_id'])
        if self.lgr_info.is_set:
            return HttpResponseBadRequest('Cannot edit LGR set')

        scripts = get_all_scripts_from_repertoire(self.lgr_info.lgr.unicode_database)
        self.initial['scripts'] = [(s, s) for s in sorted(scripts)]

        return super(AddCodepointFromScriptView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        self.template_name = 'lgr_editor/add_list.html'

        lgr = self.lgr_info.lgr
        cd = form.cleaned_data
        script = cd['script']
        validating_repertoire = get_by_name(cd['validating_repertoire'])
        validating_repertoire.expand_ranges()  # need to get through all code points

        codepoints = []
        for char in validating_repertoire.repertoire.all_repertoire():
            # XXX: Assume validating repertoire only contains single CP
            cp = char.cp[0]
            if script == self.lgr_info.lgr.unicode_database.get_script(cp, alpha4=True):
                try:
                    lgr.get_char(cp)
                except LGRException:
                    codepoints.append(cp)

        fake_lgr = LGR(name=script)
        fake_lgr.add_codepoints(codepoints)
        return self._handle_discrete(lgr, fake_lgr, cd['manual_import'])
