# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from lgr.tools.utils import parse_label_input
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_models.models.unicode import UnicodeVersion
from lgr_utils import unidb


class LabelFormsForm(forms.Form):
    label = forms.CharField(label=_("Label"))
    unicode_version = forms.ModelChoiceField(label=_("Unicode version"),
                                             required=True,
                                             help_text=_('The unicode version used'),
                                             queryset=UnicodeVersion.get_activated(),
                                             empty_label=None)

    def clean(self):
        label = self.cleaned_data['label']
        unicode_version: UnicodeVersion = self.cleaned_data['unicode_version']
        udata = unidb.manager.get_db_by_version(unicode_version.version)
        try:
            value = parse_label_input(label, idna_decoder=udata.idna_decode_label)
        except ValueError as e:
            self.add_error('label', lgr_exception_to_text(e))
        else:
            self.cleaned_data['label'] = value
        return self.cleaned_data
