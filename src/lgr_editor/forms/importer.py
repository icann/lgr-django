# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django import forms
from .fields import (DEFAULT_UNICODE_VERSION,
                     VALIDATING_REPERTOIRES,
                     DEFAULT_VALIDATING_REPERTOIRE)


class CreateLGRForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    validating_repertoire = forms.ChoiceField(label=_("Validating repertoire"),
                                              help_text=_('Code points will be limited to the selected repertoire'),
                                              required=False,
                                              choices=(('', ''),) + VALIDATING_REPERTOIRES,
                                              initial=DEFAULT_VALIDATING_REPERTOIRE)
    unicode_version = forms.CharField(widget=forms.HiddenInput(),
                                      initial=DEFAULT_UNICODE_VERSION)


class ImportLGRForm(forms.Form):
    file = forms.FileField(label=_("Select a file"))
    validating_repertoire = forms.ChoiceField(label=_("Validating repertoire"),
                                              help_text=_('Code points will be limited to the selected repertoire'),
                                              required=False,
                                              choices=(('', ''),) + VALIDATING_REPERTOIRES,
                                              initial=DEFAULT_VALIDATING_REPERTOIRE)
