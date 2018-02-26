# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from lgr_editor import unidb

from lgr.tools.utils import parse_label_input


class LabelFormsForm(forms.Form):
    label = forms.CharField(label=_("Label"))
    unicode_version = forms.ChoiceField(label=_("Unicode version"),
                                        required=True,
                                        help_text=_('The unicode version used'))

    def __init__(self, *args, **kwargs):
        unicode_versions = kwargs.pop('unicode_versions', None)
        super(LabelFormsForm, self).__init__(*args, **kwargs)
        if unicode_versions is not None:
            self.fields['unicode_version'].choices = unicode_versions

    def clean(self):
        label = self.cleaned_data['label']
        unicode_version = self.cleaned_data['unicode_version']
        udata = unidb.manager.get_db_by_version(unicode_version)
        try:
            value = parse_label_input(label, idna_decoder=udata.idna_decode_label)
        except ValueError as e:
            self.add_error('label', unicode(e))
        else:
            self.cleaned_data['label'] = value
        return self.cleaned_data
