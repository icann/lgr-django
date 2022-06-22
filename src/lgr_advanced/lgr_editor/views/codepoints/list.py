#! /bin/env python
# -*- coding: utf-8 -*-
"""
list.py - 
"""
import logging
from io import StringIO

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, FormView
from django.views.generic.base import View

from lgr.char import RangeChar
from lgr.exceptions import LGRException, LGRFormatException, CharInvalidContextRule
from lgr.utils import format_cp
from lgr.validate import check_symmetry, check_transitivity
from lgr_advanced.lgr_editor.forms import (AddCodepointForm,
                                           EditCodepointsForm)
from lgr_advanced.lgr_editor.utils import slug_to_cp, render_char
from lgr_advanced.lgr_editor.views.codepoints.mixins import CodePointMixin
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin, LGREditMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_utils import unidb
from lgr_utils.cp import render_name, cp_to_slug

logger = logging.getLogger(__name__)


class CodePointsViewMixin:

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        has_range = False
        for char in self.lgr.repertoire.all_repertoire():
            if isinstance(char, RangeChar):
                has_range = True
                break

        rule_names = (('', ''),) + tuple((v, v) for v in self.lgr.rules)
        cp_form = None
        edit_codepoints_form = None
        form = ctx.get('form')
        if form:
            if isinstance(form, AddCodepointForm):
                cp_form = form
            elif isinstance(form, EditCodepointsForm):
                edit_codepoints_form = form
        cp_form = cp_form or AddCodepointForm(prefix='add_cp')
        edit_codepoints_form = edit_codepoints_form or EditCodepointsForm(prefix='edit_codepoints',
                                                                          rule_names=rule_names,
                                                                          tags=((v, v) for v in
                                                                                self.lgr.all_tags()))
        ctx.update({
            'cp_form': cp_form,
            'edit_codepoints_form': edit_codepoints_form,
            'has_range': has_range,
        })
        return ctx


class ListCodePointsView(LGRHandlingBaseMixin, CodePointsViewMixin, TemplateView):
    """
    List the codepoints defined in an LGR.
    """
    template_name = 'lgr_editor/codepoint_list.html'

    def post(self, request, *args, **kwargs):
        if 'add_cp' in request.POST:
            view = AddCodePointView.as_view()
        elif 'add-rules' in request.POST or 'add-tags' in request.POST:
            view = EditCodePointView.as_view()
        else:
            raise Http404

        return view(request, *args, **kwargs)


class AddCodePointView(LGREditMixin, CodePointsViewMixin, FormView):
    form_class = AddCodepointForm
    template_name = 'lgr_editor/codepoint_list.html'

    def get_prefix(self):
        return 'add_cp'

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_pk': self.lgr_pk, 'model': self.lgr_object.model_name})

    def form_valid(self, form):
        logger.debug("Add CP")
        # form was submitted, we parse the value from the form field
        cp_or_sequence = form.cleaned_data['codepoint']
        override_repertoire = form.cleaned_data['override_repertoire']
        try:
            self.lgr.add_cp(cp_or_sequence,
                            validating_repertoire=self.validating_repertoire,
                            override_repertoire=override_repertoire)
            self.update_lgr()
            messages.success(self.request, _('New code point %s added') % format_cp(cp_or_sequence))
        except LGRException as ex:
            messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
            # do nothing to redirect to myself (success url) to refresh display
            # Note: cannot add code point in set mode

        return super().form_valid(form)


class EditCodePointView(LGREditMixin, CodePointsViewMixin, FormView):
    form_class = EditCodepointsForm
    template_name = 'lgr_editor/codepoint_list.html'

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_pk': self.lgr_pk, 'model': self.lgr_object.model_name})

    def get_prefix(self):
        return 'edit_codepoints'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        rule_names = (('', ''),) + tuple((v, v) for v in self.lgr.rules)
        kwargs['rule_names'] = rule_names
        kwargs['tags'] = tuple((v, v) for v in self.lgr.all_tags())
        return kwargs

    def form_valid(self, form):
        logger.debug('Edit codepoints')
        cd = form.cleaned_data
        when = cd['when'] or None
        not_when = cd['not_when'] or None
        tags = cd['tags']
        edited = cd['cp_id']
        invalid = []
        for cp in [slug_to_cp(c) for c in edited]:
            char = self.lgr.get_char(cp)
            new_tags = char.tags + tags

            try:
                if isinstance(char, RangeChar):
                    # Delete codepoint range from LGR, then add it
                    self.lgr.del_range(char.first_cp, char.last_cp)
                    self.lgr.add_range(char.first_cp,
                                       char.last_cp,
                                       comment=char.comment,
                                       when=when or char.when, not_when=not_when or char.not_when,
                                       ref=char.references,
                                       tag=new_tags)
                else:
                    # Delete codepoint from LGR, then add it + its variants
                    self.lgr.del_cp(char.cp)
                    self.lgr.add_cp(char.cp,
                                    comment=char.comment,
                                    ref=char.references,
                                    tag=new_tags,
                                    when=when or char.when, not_when=not_when or char.not_when)
                    for variant in char.get_variants():
                        self.lgr.add_variant(char.cp,
                                             variant.cp,
                                             variant_type=variant.type,
                                             when=variant.when, not_when=variant.not_when,
                                             comment=variant.comment, ref=variant.references)
            except (LGRFormatException, CharInvalidContextRule) as e:
                logger.warning('Cannot update char tags/wle:', exc_info=e)
                invalid.append(char)
                # Need to revert the deletion
                if isinstance(char, RangeChar):
                    self.lgr.add_range(char.first_cp,
                                       char.last_cp,
                                       comment=char.comment,
                                       when=char.when, not_when=char.not_when,
                                       ref=char.references,
                                       tag=char.tags)
                else:
                    self.lgr.add_cp(char.cp,
                                    comment=char.comment,
                                    ref=char.references,
                                    tag=char.tags,
                                    when=char.when, not_when=char.not_when)
                    for variant in char.get_variants():
                        self.lgr.add_variant(char.cp,
                                             variant.cp,
                                             variant_type=variant.type,
                                             when=variant.when, not_when=variant.not_when,
                                             comment=variant.comment, ref=variant.references)

        self.update_lgr()
        operation = _('Rule') if 'add-rules' in self.request.POST else _('Tag(s)')
        operation_lowercase = _('rule') if 'add-rules' in self.request.POST else _('tag(s)')
        if len(edited) - len(invalid):
            messages.add_message(self.request,
                                 messages.SUCCESS,
                                 _("%(operation)s successfully added to %(nb_cp)s code point(s)") % {
                                     'operation': operation,
                                     'nb_cp': len(edited) - len(invalid)})
        if invalid:
            messages.add_message(self.request,
                                 messages.WARNING,
                                 _("%(nb_cp)s code points were not updated to avoid invalid %(operation)s") % {
                                     'operation': operation_lowercase,
                                     'nb_cp': len(invalid)})

        return super().form_valid(form)


class ListCodePointsJsonView(LGRHandlingBaseMixin, View):

    def get(self, request, *args, **kwargs):
        udata = unidb.manager.get_db_by_version(self.lgr.metadata.unicode_version)

        repertoire = self.lgr_object.get_repertoire_cache()
        if repertoire is None:
            # Generate repertoire
            repertoire = []
            for char in self.lgr.repertoire:
                actions = []
                prop = ''
                for c in char.cp:
                    prop = udata.get_idna_prop(c)
                    if prop in ['UNASSIGNED', 'DISALLOWED']:
                        break
                cp_slug = cp_to_slug(char.cp)
                if prop not in ['UNASSIGNED', 'DISALLOWED']:
                    kwargs = {'lgr_pk': self.lgr_pk, 'codepoint_id': cp_slug, 'model': self.lgr_object.model_name}
                    cp_view_url = reverse('codepoint_view', kwargs=kwargs)
                    actions.append(cp_view_url)
                is_range = isinstance(char, RangeChar)
                if is_range:
                    expand_url = reverse('expand_range', kwargs={'lgr_pk': self.lgr_pk,
                                                                 'codepoint_id': cp_slug})
                    actions.append(expand_url)

                repertoire.append({
                    'codepoint_id': cp_slug,
                    'cp_disp': render_char(char),
                    'comment': char.comment or '',
                    'name': render_name(char, udata) or prop,
                    'tags': char.tags,
                    'variant_number': len(list(char.get_variants())),
                    'is_range': is_range,
                    'actions': actions,
                    'idna_property': prop
                })
            self.lgr_object.set_repertoire_cache(repertoire)

        response = {'data': repertoire}

        return JsonResponse(response)


class ExpandRangesView(LGREditMixin, View):
    """
    Expand all ranges into code points.
    """

    def get(self, request, *args, **kwargs):
        try:
            self.lgr.expand_ranges()
        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))

        self.update_lgr()
        return redirect('codepoint_list', lgr_pk=self.lgr_pk, model=self.lgr_object.model_name)


class ExpandRangeView(LGREditMixin, CodePointMixin, View):
    """
    Expand a range into code points.
    """

    def get(self, request, *args, **kwargs):
        char = self.lgr.get_char(self.codepoint)

        if not isinstance(char, RangeChar):
            logger.error("Cannot expand non-range code point")
            return redirect('codepoint_list', lgr_pk=self.lgr_pk, model=self.lgr_object.model_name)

        try:
            self.lgr.expand_range(char.first_cp, char.last_cp)
        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))

        self.update_lgr()
        return redirect('codepoint_list', lgr_pk=self.lgr_pk, model=self.lgr_object.model_name)


class PopulateVariantsView(LGREditMixin, View):
    """
    Automatically populate variants to achieve transitivity and symmetry.
    """

    def get(self, request, *args, **kwargs):
        if 'test' in request.GET:
            return JsonResponse({
                'result': check_symmetry(self.lgr, None)[0] and check_transitivity(self.lgr, None)[0]
            })

        log_output = StringIO()
        ch = logging.StreamHandler(log_output)
        ch.setLevel(logging.INFO)
        populate_logger = logging.getLogger('lgr.populate')

        # Configure module logger - since user may have disabled the 'lgr' logger,
        # reset its level
        populate_logger.addHandler(ch)
        populate_logger.setLevel('INFO')
        self.lgr.populate_variants()
        messages.add_message(request, messages.INFO, log_output.getvalue())
        messages.add_message(request, messages.SUCCESS, _("Variants populated"))
        populate_logger.removeHandler(ch)
        log_output.close()
        self.update_lgr()
        return redirect('codepoint_list', lgr_pk=self.lgr_pk, model=self.lgr_object.model_name)
