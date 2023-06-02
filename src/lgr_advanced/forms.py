# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_editor.forms import FILE_FIELD_ENCODING_HELP


class LabelFormsForm(forms.Form):
    labels = forms.FileField(label=_("Labels"),
                             help_text=FILE_FIELD_ENCODING_HELP,
                             required=True)
