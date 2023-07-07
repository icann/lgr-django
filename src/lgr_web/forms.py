# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.translation import ugettext_lazy as _

from lgr.tools.utils import parse_label_input
from lgr_advanced.lgr_editor.forms.fields import LABEL_FILE_HELP, LABEL_INPUT_HELP
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_utils import unidb


class LabelFormsForm(forms.Form):
    label = forms.CharField(label=_("Label"),
                            help_text=LABEL_INPUT_HELP)

    def clean(self):
        label = self.cleaned_data['label']
        udata = unidb.manager.get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)
        try:
            value = parse_label_input(label, idna_decoder=udata.idna_decode_label)
        except ValueError as e:
            self.add_error('label', lgr_exception_to_text(e))
        else:
            self.cleaned_data['label'] = value

        return self.cleaned_data


class LabelFileFormsForm(forms.Form):
    labels = forms.FileField(label=_("Labels"),
                             help_text=LABEL_FILE_HELP,
                             required=True,
                             validators=[FileExtensionValidator(allowed_extensions=('', 'txt',))],
                             widget=forms.FileInput(attrs={'accept': 'text/plain'}))
