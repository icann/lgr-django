#! /bin/env python
# -*- coding: utf-8 -*-
"""
metadata - 
"""
import logging

from dal import autocomplete
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from lgr.exceptions import LGRException
from lgr.metadata import Scope, Metadata, Version, Description
from lgr_advanced.api import get_builtin_or_session_repertoire
from lgr_advanced.lgr_editor.forms import MetadataForm, LanguageFormSet, IANA_LANG_REGISTRY
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text

logger = logging.getLogger(__name__)


class MetadataView(LGRHandlingBaseMixin, FormView):
    """
    This view is used to display the metadata screen.
    """
    form_class = MetadataForm
    template_name = 'lgr_editor/metadata.html'

    def get_form_kwargs(self):
        kwargs = super(MetadataView, self).get_form_kwargs()

        metadata = self.lgr_info.lgr.metadata
        language = metadata.languages[0] if len(metadata.languages) > 0 else ""
        scope = metadata.scopes[0] if len(metadata.scopes) > 0 else Scope('')

        description = ""
        description_type = ""
        if metadata.description is not None:
            description = metadata.description.value
            description_type = metadata.description.description_type or ""

        validating_repertoire_name = ""
        if self.lgr_info.validating_repertoire is not None:
            validating_repertoire_name = self.lgr_info.validating_repertoire.name

        kwargs['initial'] = {
            'version': metadata.version.value if metadata.version else "",
            'version_comment': metadata.version.comment if metadata.version else "",
            'date': metadata.date,
            'language': language,
            'scope': scope.value,
            'scope_type': scope.scope_type,
            'unicode_version': metadata.unicode_version,
            'validity_start': metadata.validity_start,
            'validity_end': metadata.validity_end,
            'description': description,
            'description_type': description_type,
            'validating_repertoire': validating_repertoire_name,
        }

        # add other repertoires available in the user's session
        kwargs['additional_repertoires'] = [lgr['name'] for lgr in self.session.list_lgr()
                                            if lgr['name'] != self.lgr_info.name]

        kwargs['disabled'] = self.kwargs.get('lgr_set_id') is not None

        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(MetadataView, self).get_context_data(**kwargs)
        ctx['lgr_id'] = self.kwargs['lgr_id']
        ctx['lgr'] = self.lgr_info.lgr
        language_formset = LanguageFormSet(self.request.POST or None,
                                           prefix='lang',
                                           initial=[{'language': l} for l in
                                                    self.lgr_info.lgr.metadata.languages],
                                           disabled=self.kwargs.get('lgr_set_id') is not None)
        if self.kwargs.get('lgr_set_id'):
            # do not enable to update references for LGRs in a set => do not need an extra widget
            language_formset.extra = 0

        ctx['language_formset'] = language_formset

        ctx['is_set'] = self.lgr_info.is_set or self.kwargs.get('lgr_set_id')

        if self.kwargs.get('lgr_set_id'):
            ctx['lgr_set_id'] = self.kwargs['lgr_set_id']
            ctx['lgr_set'] = self.session.select_lgr(self.kwargs.get('lgr_set_id')).lgr
        return ctx

    def get_success_url(self):
        return reverse('metadata', kwargs={'lgr_id': self.lgr_id})

    def form_valid(self, form):
        # main `MetadataForm` is valid, now test for `LanguageFormSet`
        language_formset = LanguageFormSet(self.request.POST, prefix='lang')
        cd = form.cleaned_data
        metadata = Metadata()

        try:
            if cd['version']:
                metadata.version = Version(cd['version'], cd['version_comment'] or None)
            else:
                metadata.version = None

            if cd['date']:
                metadata.set_date(cd['date'].isoformat())

            if cd['scope']:
                scope = Scope(value=cd['scope'],
                              scope_type=cd['scope_type'] or None)
                if len(metadata.scopes) > 0:
                    metadata.scopes[0] = scope
                else:
                    metadata.scopes.append(scope)
            if cd['unicode_version']:
                metadata.set_unicode_version(cd['unicode_version'])
            if cd['validity_start']:
                metadata.set_validity_start(cd['validity_start'].isoformat())
            if cd['validity_end']:
                metadata.set_validity_end(cd['validity_end'].isoformat())
            if cd['description']:
                metadata.description = Description(value=cd['description'],
                                                   description_type=cd['description_type'] or None)

            if cd['validating_repertoire']:
                self.lgr_info.validating_repertoire = get_builtin_or_session_repertoire(self.session,
                                                                                        cd['validating_repertoire'])
            else:
                self.lgr_info.validating_repertoire = None

            if language_formset.is_valid():
                # save languages
                metadata.set_languages(filter(None, (f.get('language') for f in language_formset.cleaned_data)))

            self.lgr_info.lgr.metadata = metadata
            self.session.save_lgr(self.lgr_info)
            messages.add_message(self.request, messages.SUCCESS, _("Meta data saved"))
        except LGRException as ex:
            messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
            return self.form_invalid(form)

        return super().form_valid(form)


class LanguageAutocomplete(autocomplete.Select2ListView):

    def get_list(self):
        return sorted(IANA_LANG_REGISTRY)
