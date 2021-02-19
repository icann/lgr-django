#! /bin/env python
# -*- coding: utf-8 -*-
"""
codepoint - 
"""
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseBadRequest, Http404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from django.views.generic.base import RedirectView, TemplateView

from lgr.char import RangeChar
from lgr.exceptions import LGRException, NotInLGR
from lgr.utils import format_cp
from lgr_advanced import unidb
from lgr_advanced.lgr_editor.forms import (AddVariantForm,
                                           CodepointForm,
                                           CodepointVariantFormSet)
from lgr_advanced.lgr_editor.utils import slug_to_cp, render_char, var_to_slug, render_age, slug_to_var
from lgr_advanced.lgr_editor.views.codepoints.mixins import LGREditMixin, CodePointMixin
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.utils import (cp_to_slug,
                                render_name)

logger = logging.getLogger(__name__)


class CodePointView(LGRHandlingBaseMixin, CodePointMixin, TemplateView):
    """
    View a specific code point of an LGR.
    """
    template_name = 'lgr_editor/codepoint_view.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        udata = unidb.manager.get_db_by_version(self.lgr_info.lgr.metadata.unicode_version)
        char = self.lgr_info.lgr.get_char(self.codepoint)
        variants = []
        for v in char.get_variants():
            in_lgr = True
            try:
                self.lgr_info.lgr.get_char(v.cp)
            except NotInLGR:
                in_lgr = False

            variants.append({
                'cp': cp_to_slug(v.cp),
                'slug': var_to_slug(v),
                'cp_disp': render_char(v),
                'name': render_name(v, udata),
                'age': render_age(v, udata),
                'when': v.when,
                'not_when': v.not_when,
                'type': v.type,
                'comment': v.comment or '',
                'references': v.references,
                'in_lgr': in_lgr
            })

        # References
        cp_references = []
        for ref_id in char.references:
            ref = self.lgr_info.lgr.reference_manager.get(str(ref_id), None)
            if ref is None:
                # Invalid reference id
                continue

            cp_references.append({
                'ref_id': ref_id,
                'description': ref.get('value', ''),
                'comment': ref.get('comment', '')
            })

        rule_names = (('', ''),) + tuple((v, v) for v in self.lgr_info.lgr.rules)
        ctx.update({
            'add_variant_form': AddVariantForm(prefix='add_variant'),
            'codepoint_form': CodepointVariantFormSet(initial=variants,
                                                      prefix='variants',
                                                      rules=rule_names,
                                                      disabled=self.lgr_info.is_set or self.lgr_set_id is not None),
            'variants_form': CodepointForm(initial={'comment': char.comment,
                                                    'tags': ' '.join(char.tags),
                                                    'when': char.when,
                                                    'not_when': char.not_when},
                                           prefix='edit_cp',
                                           rules=rule_names,
                                           disabled=self.lgr_info.is_set or self.lgr_set_id is not None),
            'is_range': isinstance(char, RangeChar),
            'cp': self.codepoint_id,
            'lgr': self.lgr_info.lgr,
            'lgr_id': self.lgr_id,
            'variants': variants,
            'cp_references': cp_references,
            'cp_references_json': json.dumps(cp_references),
            'cp_disp': render_char(char),
            'all_tags_json': json.dumps(self.lgr_info.lgr.all_tags()),
            'name': render_name(char, udata),
            'age': render_age(char, udata),
            'is_set': self.lgr_info.is_set or self.lgr_set_id is not None
        })
        if self.lgr_set_id:
            lgr_set_info = self.session.select_lgr(self.lgr_set_id)
            ctx['lgr_set'] = lgr_set_info.lgr
            ctx['lgr_set_id'] = self.lgr_set_id
        return ctx

    def post(self, request, *args, **kwargs):
        if 'add_variant' in request.POST:
            view = AddVariantView.as_view()
        elif 'edit_cp' in request.POST:
            view = EditCodePointView.as_view()
        else:
            raise Http404

        return view(request, *args, **kwargs)


class AddVariantView(LGREditMixin, CodePointMixin, FormView):
    form_class = AddVariantForm
    template_name = 'lgr_editor/codepoint_view.html'

    def get_prefix(self):
        return 'add_variant'

    def get_success_url(self):
        return reverse('codepoint_view', kwargs={'lgr_id': self.lgr_id, 'codepoint_id': self.codepoint_id})

    def form_valid(self, form):
        add_variant_form = AddVariantForm(self.request.POST, prefix='add_variant')
        logger.debug('Add variant')
        if add_variant_form.is_valid():
            var_cp_sequence = add_variant_form.cleaned_data['codepoint']
            override_repertoire = add_variant_form.cleaned_data['override_repertoire']
            try:
                self.lgr_info.lgr.add_variant(self.codepoint,
                                              var_cp_sequence,
                                              variant_type=settings.DEFAULT_VARIANT_TYPE,
                                              validating_repertoire=self.lgr_info.validating_repertoire,
                                              override_repertoire=override_repertoire)
                if var_cp_sequence not in lgr_info.lgr.repertoire:
                    # Added variant code point not in repertoire
                    # -> add it to the LGR
                    self.lgr_info.lgr.add_cp(var_cp_sequence,
                                             comment="Automatically added from out-of-repertoire variant")
                    self.lgr_info.lgr.add_variant(var_cp_sequence, self.codepoint,
                                                  variant_type=settings.DEFAULT_VARIANT_TYPE,
                                                  comment="Automatically added to map back to out-of-repertoire variant")
                    # Add identity mapping for newly added code point
                    self.lgr_info.lgr.add_variant(var_cp_sequence, var_cp_sequence,
                                                  variant_type='out-of-repertoire-var',
                                                  comment='Out-of-repertoire-var')
                    messages.success(self.request,
                                     _('Automatically added codepoint %s from out-of-repertoire-var variant') %
                                     format_cp(var_cp_sequence))
                self.session.save_lgr(self.lgr_info)
                messages.success(self.request, _('New variant %s added') % format_cp(var_cp_sequence))
            except LGRException as ex:
                messages.add_message(self.request, messages.ERROR,
                                     lgr_exception_to_text(ex))
                # do nothing to redirect to myself (success url) to refresh display
        else:
            logger.error('Add variant: form is not valid')
            logger.error(add_variant_form.errors)
        return super().form_valid(form)


class EditCodePointView(LGREditMixin, CodePointMixin, FormView):
    form_class = CodepointVariantFormSet
    template_name = 'lgr_editor/codepoint_view.html'

    def get_prefix(self):
        return 'edit_cp'

    def get_success_url(self):
        return reverse('codepoint_view', kwargs={'lgr_id': self.lgr_id, 'codepoint_id': self.codepoint_id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        rule_names = (('', ''),) + tuple((v, v) for v in self.lgr_info.lgr.rules)
        kwargs['rule_names'] = rule_names
        return kwargs

    def form_valid(self, form):
        logger.debug('Edit CP')
        variants_form = CodepointVariantFormSet(self.request.POST,
                                                prefix='variants',
                                                rules=self.rule_names,
                                                disabled=self.lgr_info.is_set or self.lgr_set_id is not None)

        comment = form.cleaned_data['comment'] or None
        char = self.lgr_info.lgr.get_char(self.codepoint)
        when = form.cleaned_data['when'] or None
        not_when = form.cleaned_data['not_when'] or None
        ref = char.references
        tag = form.cleaned_data['tags'].split()

        try:
            if isinstance(char, RangeChar):
                self.lgr_info.lgr.del_range(char.first_cp, char.last_cp)
                # No validating repertoire since
                # the codepoint is being edited
                self.lgr_info.lgr.add_range(char.first_cp,
                                            char.last_cp,
                                            comment=comment,
                                            when=when, not_when=not_when,
                                            ref=ref,
                                            tag=tag)
            else:
                if variants_form.is_valid():
                    # Delete codepoint from LGR, then add it + its variants
                    self.lgr_info.lgr.del_cp(self.codepoint)
                    # No validating repertoire here neither
                    self.lgr_info.lgr.add_cp(self.codepoint,
                                             comment=comment,
                                             ref=ref,
                                             tag=tag,
                                             when=when, not_when=not_when)
                    for v_form in variants_form:
                        variant_codepoint = slug_to_cp(v_form.cleaned_data['cp'])
                        variant_comment = v_form.cleaned_data['comment'] or None
                        variant_type = v_form.cleaned_data['type']
                        variant_when = v_form.cleaned_data['when'] or None
                        variant_not_when = v_form.cleaned_data['not_when'] or None
                        # No validating repertoire here neither
                        self.lgr_info.lgr.add_variant(self.codepoint,
                                                      variant_codepoint,
                                                      comment=variant_comment,
                                                      variant_type=variant_type,
                                                      when=variant_when,
                                                      not_when=variant_not_when)
                else:
                    logger.error('Edit CP: form is not valid')
                    logger.error(variants_form.errors)

            # Save edition
            self.session.save_lgr(self.lgr_info)
            messages.success(self.request, _('Code point edited'))
            # do nothing to redirect to myself (success url) to refresh display
        except LGRException as ex:
            messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
            # do nothing to redirect to myself (success url) to refresh display

        return super().form_valid(form)


class CodePointUpdateReferencesView(LGREditMixin, CodePointMixin, RedirectView):
    """
    Update a codepoint's references.
    """
    pattern_name = 'codepoint_view'

    def post(self, request, *args, **kwargs):
        ref_ids = filter(None,
                         request.POST.getlist('ref_id'))  # filter away empty entries (an artifact of the editing form)

        try:
            char = self.lgr_info.lgr.get_char(self.codepoint)
            tags = char.tags
            comment = char.comment

            if isinstance(char, RangeChar):
                self.lgr_info.lgr.del_range(char.first_cp,
                                            char.last_cp)
                # No validating repertoire here since we're only updating references
                self.lgr_info.lgr.add_range(char.first_cp,
                                            char.last_cp,
                                            comment=comment,
                                            when=char.when,
                                            not_when=char.not_when,
                                            ref=ref_ids,  # update the ref ids
                                            tag=tags)
            else:
                self.lgr_info.lgr.del_cp(self.codepoint)
                # No validating repertoire either
                self.lgr_info.lgr.add_cp(self.codepoint,
                                         comment=char.comment,
                                         when=char.when, not_when=char.not_when,
                                         ref=ref_ids,  # update the ref ids
                                         tag=tags)
                for var in char.get_variants():
                    # add back the variants
                    self.lgr_info.lgr.add_variant(self.codepoint,
                                                  variant_cp=var.cp,
                                                  variant_type=var.type,
                                                  when=var.when,
                                                  not_when=var.not_when,
                                                  comment=var.comment,
                                                  ref=var.references)
            self.session.save_lgr(self.lgr_info)
            messages.success(request, _('References updated successfully'))
        except LGRException as ex:
            messages.add_message(request, messages.ERROR, lgr_exception_to_text(ex))

        return super().post(request, *args, **kwargs)


class VariantUpdateReferencesView(LGREditMixin, CodePointMixin, RedirectView):
    """
    Update a variant's references.
    """
    pattern_name = 'codepoint_view'

    def post(self, request, *args, **kwargs):
        var_cp, var_when, var_not_when = slug_to_var(self.kwargs['var_slug'])
        ref_ids = filter(None,
                         self.request.POST.getlist(
                             'ref_id'))  # filter away empty entries (an artifact of the editing form)

        try:
            char = self.lgr_info.lgr.get_char(self.codepoint)
            # find our variant
            for variant in char.get_variants():
                if variant.cp == var_cp and variant.when == (var_when or None) and variant.not_when == (
                        var_not_when or None):
                    # found it!
                    char.del_variant(variant.cp, when=variant.when, not_when=variant.not_when)
                    self.lgr_info.lgr.add_variant(self.codepoint,
                                                  variant.cp,
                                                  variant_type=variant.type,
                                                  when=variant.when,
                                                  not_when=variant.not_when,
                                                  comment=variant.comment,
                                                  ref=ref_ids)
                    self.session.save_lgr(self.lgr_info)
                    messages.success(self.request,
                                     _('References updated successfully'))
                    break
            else:
                errmsg = _("Variant %(var_codepoint)s for code point %(codepoint)s "
                           "with when=%(when)s and "
                           "not-when=%(not_when)s could not be found") % {
                             'var_codepoint': var_cp,
                             'codepoint': self.codepoint_id,
                             'when': var_when,
                             'not_when': var_not_when,
                         }
                messages.error(request, errmsg)

        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))

        return super().post(request, *args, **kwargs)


class CodePointDeleteView(LGREditMixin, CodePointMixin, RedirectView):
    """
    Delete a codepoint from an LGR.
    """
    pattern_name = 'codepoint_view'

    # TODO - only accept POST request
    def get(self, request, *args, **kwargs):
        char = self.lgr_info.lgr.get_char(self.codepoint)

        try:
            if isinstance(char, RangeChar):
                self.lgr_info.lgr.del_range(char.first_cp, char.last_cp)
            else:
                self.lgr_info.lgr.del_cp(self.codepoint)
            self.session.save_lgr(self.lgr_info)
            messages.info(self.request, _("Code point %s has been deleted") % format_cp(self.codepoint))
        except LGRException as ex:
            messages.add_message(self.request, messages.ERROR,
                                 lgr_exception_to_text(ex))

        return super().get(request, *args, **kwargs)


class VariantDeleteView(LGREditMixin, CodePointMixin, RedirectView):
    """
    Delete a variant of a codepoint from an LGR.
    """
    pattern_name = 'codepoint_view'

    # TODO - only accept POST request
    def get(self, request, *args, **kwargs):
        var_slug = self.kwargs['var_slug']
        lgr_info = self.session.select_lgr(self.lgr_id)
        if lgr_info.is_set:
            return HttpResponseBadRequest('Cannot edit LGR set')

        var_cp, var_when, var_not_when = slug_to_var(var_slug)

        try:
            r = lgr_info.lgr.del_variant(self.codepoint, var_cp, when=var_when or None, not_when=var_not_when or None)
            var_msg_prefix = _("Variant %(var_cp)s with when='%(when)s' and not-when='%(not_when)s'") \
                             % {'var_cp': format_cp(var_cp),
                                'when': var_when,
                                'not_when': var_not_when}
            if r:
                self.session.save_lgr(lgr_info)
                messages.info(request, _("%(var_msg_prefix)s has been deleted") % {'var_msg_prefix': var_msg_prefix})
            else:
                messages.error(request,
                               _("%(var_msg_prefix)s could not be deleted because it was not found")
                               % {'var_msg_prefix': var_msg_prefix})
        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))

        return super().get(request, *args, **kwargs)
