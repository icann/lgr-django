#! /bin/env python
# -*- coding: utf-8 -*-
"""
metadata - 
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from lgr.exceptions import LGRException
from lgr.metadata import Scope, Metadata, Version, Description
from lgr_advanced.lgr_editor.forms import MetadataForm, LanguageFormSet
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.models import LgrModel
from lgr_models.models.lgr import LgrBaseModel

logger = logging.getLogger(__name__)


class MetadataView(LGRHandlingBaseMixin, FormView):
    """
    This view is used to display the metadata screen.
    """
    form_class = MetadataForm
    template_name = 'lgr_editor/metadata.html'

    def get_initial(self):
        initial = super().get_initial()

        metadata = self.lgr.metadata
        metadata.set_unicode_version(settings.SUPPORTED_UNICODE_VERSION)
        language = metadata.languages[0] if len(metadata.languages) > 0 else ""
        scope = metadata.scopes[0] if len(metadata.scopes) > 0 else Scope('')

        description = ""
        description_type = ""
        if metadata.description is not None:
            description = metadata.description.value
            description_type = metadata.description.description_type or ""

        initial.update({
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
            'validating_repertoire': [self.validating_repertoire.to_tuple()
                                      if self.validating_repertoire else ('', '')],
        })
        return initial

    def get_form_kwargs(self):
        kwargs = super(MetadataView, self).get_form_kwargs()

        # add other repertoires available in the user's session
        kwargs['additional_repertoires'] = LgrModel.objects.filter(owner=self.request.user).exclude(
            name=self.lgr_object.name)

        kwargs['disabled'] = self.lgr_is_in_set()

        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(MetadataView, self).get_context_data(**kwargs)
        language_formset = LanguageFormSet(self.request.POST or None,
                                           prefix='lang',
                                           initial=[{'language': l} for l in
                                                    self.lgr.metadata.languages],
                                           disabled=self.lgr_is_in_set())
        if self.lgr_is_in_set():
            # do not enable to update metadata for LGRs in a set => do not need an extra widget
            language_formset.extra = 0

        ctx.update({
            'language_formset': language_formset
        })

        return ctx

    def get_success_url(self):
        return reverse('metadata', kwargs={'lgr_pk': self.lgr_pk, 'model': self.lgr_object.model_name})

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
            if cd['validity_start']:
                metadata.set_validity_start(cd['validity_start'].isoformat())
            if cd['validity_end']:
                metadata.set_validity_end(cd['validity_end'].isoformat())
            if cd['description']:
                metadata.description = Description(value=cd['description'],
                                                   description_type=cd['description_type'] or None)

            self.lgr_object.validating_repertoire = LgrBaseModel.from_tuple(cd['validating_repertoire'],
                                                                            user=self.request.user)
            if language_formset.is_valid():
                # save languages
                metadata.set_languages(filter(None, (f.get('language') for f in language_formset.cleaned_data)))

            self.lgr.metadata = metadata
            self.update_lgr()
            messages.add_message(self.request, messages.SUCCESS, _("Meta data saved"))
        except LGRException as ex:
            messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
            return self.form_invalid(form)

        return super().form_valid(form)
