#! /bin/env python
# -*- coding: utf-8 -*-
"""
list.py - 
"""
import json
import logging
from io import StringIO

from django.contrib import messages
from django.core.cache import cache
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, FormView
from django.views.generic.base import View, RedirectView

from lgr.char import RangeChar
from lgr.exceptions import LGRException, LGRFormatException, CharInvalidContextRule
from lgr.utils import format_cp
from lgr.validate import check_symmetry, check_transitivity
from lgr_advanced import unidb
from lgr_advanced.lgr_editor.forms import (AddCodepointForm,
                                           EditCodepointsForm)
from lgr_advanced.lgr_editor.utils import slug_to_cp, render_char
from lgr_advanced.lgr_editor.views.codepoints.mixins import CodePointMixin
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin, LGREditMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.utils import (make_lgr_session_key,
                                LGR_REPERTOIRE_CACHE_KEY,
                                cp_to_slug,
                                render_name,
                                LGR_CACHE_TIMEOUT)

logger = logging.getLogger(__name__)


class ListCodePointsView(LGRHandlingBaseMixin, TemplateView):
    """
    List the codepoints defined in an LGR.
    """
    template_name = 'lgr_editor/codepoint_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        has_range = False
        for char in self.lgr_info.lgr.repertoire.all_repertoire():
            if isinstance(char, RangeChar):
                has_range = True
                break

        rule_names = (('', ''),) + tuple((v, v) for v in self.lgr_info.lgr.rules)
        ctx.update({
            'cp_form': AddCodepointForm(prefix='add_cp'),
            'edit_codepoints_form': EditCodepointsForm(prefix='edit_codepoints', rule_names=rule_names),
            'lgr': self.lgr_info.lgr,
            'lgr_id': self.lgr_id,
            'is_set': self.lgr_info.is_set or self.lgr_set_id is not None,
            'has_range': has_range,
            'all_tags_json': json.dumps(self.lgr_info.lgr.all_tags()),
        })
        if self.lgr_set_id:
            lgr_set_info = self.session.select_lgr(self.lgr_set_id)
            ctx['lgr_set'] = lgr_set_info.lgr
            ctx['lgr_set_id'] = self.lgr_set_id
        return ctx

    def post(self, request, *args, **kwargs):
        if 'add_cp' in request.POST:
            view = AddCodePointView.as_view()
        elif 'add-rules' in request.POST or 'add-tags' in request.POST:
            view = EditCodePointView.as_view()
        else:
            raise Http404

        return view(request, *args, **kwargs)


class AddCodePointView(LGREditMixin, FormView):
    form_class = AddCodepointForm
    template_name = 'lgr_editor/codepoint_list.html'

    def get_prefix(self):
        return 'add_cp'

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_id': self.lgr_id})

    def form_valid(self, form):
        logger.debug("Add CP")
        # form was submitted, we parse the value from the form field
        cp_or_sequence = form.cleaned_data['codepoint']
        override_repertoire = form.cleaned_data['override_repertoire']
        try:
            self.lgr_info.lgr.add_cp(cp_or_sequence,
                                     validating_repertoire=self.lgr_info.validating_repertoire,
                                     override_repertoire=override_repertoire)
            self.session.save_lgr(self.lgr_info)
            messages.success(self.request, _('New code point %s added') % format_cp(cp_or_sequence))
        except LGRException as ex:
            messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
            # do nothing to redirect to myself (success url) to refresh display
            # Note: cannot add code point in set mode

        return super().form_valid(form)


class EditCodePointView(LGREditMixin, FormView):
    form_class = EditCodepointsForm
    template_name = 'lgr_editor/codepoint_list.html'

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_id': self.lgr_id})

    def get_prefix(self):
        return 'edit_codepoints'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        rule_names = (('', ''),) + tuple((v, v) for v in self.lgr_info.lgr.rules)
        kwargs['rule_names'] = rule_names
        return kwargs

    def form_valid(self, form):
        logger.debug('Edit codepoints')
        cd = form.cleaned_data
        when = cd['when'] or None
        not_when = cd['not_when'] or None
        tags = cd['tags'].split()
        edited = cd['cp_id']
        invalid = []
        for cp in [slug_to_cp(c) for c in edited]:
            char = self.lgr_info.lgr.get_char(cp)
            new_tags = char.tags + tags

            try:
                if isinstance(char, RangeChar):
                    # Delete codepoint range from LGR, then add it
                    self.lgr_info.lgr.del_range(char.first_cp, char.last_cp)
                    self.lgr_info.lgr.add_range(char.first_cp,
                                                char.last_cp,
                                                comment=char.comment,
                                                when=when or char.when, not_when=not_when or char.not_when,
                                                ref=char.references,
                                                tag=new_tags)
                else:
                    # Delete codepoint from LGR, then add it + its variants
                    self.lgr_info.lgr.del_cp(char.cp)
                    self.lgr_info.lgr.add_cp(char.cp,
                                             comment=char.comment,
                                             ref=char.references,
                                             tag=new_tags,
                                             when=when or char.when, not_when=not_when or char.not_when)
                    for variant in char.get_variants():
                        self.lgr_info.lgr.add_variant(char.cp,
                                                      variant.cp,
                                                      variant_type=variant.type,
                                                      when=variant.when, not_when=variant.not_when,
                                                      comment=variant.comment, ref=variant.references)
            except (LGRFormatException, CharInvalidContextRule) as e:
                logger.warning('Cannot update char tags/wle:', exc_info=e)
                invalid.append(char)
                # Need to revert the deletion
                if isinstance(char, RangeChar):
                    self.lgr_info.lgr.add_range(char.first_cp,
                                                char.last_cp,
                                                comment=char.comment,
                                                when=char.when, not_when=char.not_when,
                                                ref=char.references,
                                                tag=char.tags)
                else:
                    self.lgr_info.lgr.add_cp(char.cp,
                                             comment=char.comment,
                                             ref=char.references,
                                             tag=char.tags,
                                             when=char.when, not_when=char.not_when)
                    for variant in char.get_variants():
                        self.lgr_info.lgr.add_variant(char.cp,
                                                      variant.cp,
                                                      variant_type=variant.type,
                                                      when=variant.when, not_when=variant.not_when,
                                                      comment=variant.comment, ref=variant.references)

        self.session.save_lgr(self.lgr_info)
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
        udata = unidb.manager.get_db_by_version(self.lgr_info.lgr.metadata.unicode_version)

        repertoire_cache_key = make_lgr_session_key(LGR_REPERTOIRE_CACHE_KEY,
                                                    request,
                                                    self.lgr_id)
        repertoire = cache.get(repertoire_cache_key)
        if repertoire is None:
            # Generate repertoire
            repertoire = []
            for char in self.lgr_info.lgr.repertoire:
                cp_slug = cp_to_slug(char.cp)
                kwargs = {'lgr_id': self.lgr_id, 'codepoint_id': cp_slug}
                if self.lgr_set_id is not None:
                    kwargs['lgr_set_id'] = self.lgr_set_id
                cp_view_url = reverse('codepoint_view', kwargs=kwargs)
                actions = [cp_view_url]
                is_range = isinstance(char, RangeChar)
                if is_range:
                    expand_url = reverse('expand_range', kwargs={'lgr_id': self.lgr_id,
                                                                 'codepoint_id': cp_slug})
                    actions.append(expand_url)

                repertoire.append({
                    'codepoint_id': cp_slug,
                    'cp_disp': render_char(char),
                    'comment': char.comment or '',
                    'name': render_name(char, udata),
                    'tags': char.tags,
                    'variant_number': len(list(char.get_variants())),
                    'is_range': is_range,
                    'actions': actions
                })
            cache.set(repertoire_cache_key, repertoire, LGR_CACHE_TIMEOUT)

        response = {'data': repertoire}

        return JsonResponse(response)


class ExpandRangesView(LGREditMixin, RedirectView):
    """
    Expand all ranges into code points.
    """
    pattern_name = 'codepoint_list'

    def get(self, request, *args, **kwargs):
        try:
            self.lgr_info.lgr.expand_ranges()
        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))

        self.session.save_lgr(self.lgr_info)
        return super().get(request, *args, **kwargs)


class ExpandRangeView(LGREditMixin, CodePointMixin, View):
    """
    Expand a range into code points.
    """

    def get(self, request, *args, **kwargs):
        char = self.lgr_info.lgr.get_char(self.codepoint)

        if not isinstance(char, RangeChar):
            logger.error("Cannot expand non-range code point")
            return redirect('codepoint_list', lgr_id=self.lgr_id)

        try:
            self.lgr_info.lgr.expand_range(char.first_cp, char.last_cp)
        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))

        self.session.save_lgr(self.lgr_info)
        return redirect('codepoint_list', lgr_id=self.lgr_id)


class PopulateVariantsView(LGRHandlingBaseMixin, RedirectView):
    """
    Automatically populate variants to achieve transitivity and symmetry.
    """
    pattern_name = 'codepoint_list'

    def get(self, request, *args, **kwargs):
        lgr = self.lgr_info.lgr

        if 'test' in request.GET:
            return JsonResponse({
                'result': check_symmetry(lgr, None)[0] and check_transitivity(lgr, None)[0]
            })

        log_output = StringIO()
        ch = logging.StreamHandler(log_output)
        ch.setLevel(logging.INFO)
        populate_logger = logging.getLogger('lgr.populate')

        # Configure module logger - since user may have disabled the 'lgr' logger,
        # reset its level
        populate_logger.addHandler(ch)
        populate_logger.setLevel('INFO')
        lgr.populate_variants()
        messages.add_message(request, messages.INFO, log_output.getvalue())
        messages.add_message(request, messages.SUCCESS, _("Variants populated"))
        populate_logger.removeHandler(ch)
        log_output.close()
        self.session.save_lgr(self.lgr_info)
        return super().get(request, *args, **kwargs)
