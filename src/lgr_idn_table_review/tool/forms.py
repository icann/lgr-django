# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import FileField
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_tools.forms import UAEmailField


class LGRIdnTableReviewForm(forms.Form):
    idn_tables = FileField(label=_('Select IDN table(s) to review'),
                           help_text=_('File(s) must be encoded in UTF-8 and using UNIX line ending.'
                                       'You can select up to 20 IDN tables.'),
                           required=True,
                           widget=forms.ClearableFileInput(attrs={'multiple': True}))

    def clean_idn_tables(self):
        if len(self.files.getlist('idn_tables')) > settings.MAX_USER_IDN_REVIEW_INPUT:
            raise ValidationError(
                _('You can upload up to %(max_files)s files'),
                params={'max_files': settings.MAX_USER_IDN_REVIEW_INPUT})
        return self.cleaned_data['idn_tables']


class IdnTableReviewSelectReferenceForm(forms.Form):
    email = UAEmailField(label=_("E-mail"),
                         help_text=_('As the computing may be very long, we will warn by e-mail once the result can be '
                                     'downloaded'),
                         required=False,
                         widget=forms.TextInput(attrs={'placeholder': 'Email address for tasks results'}))

    def __init__(self, *args, **kwargs):
        idn_tables = kwargs.pop('idn_tables', [])
        lgrs = kwargs.pop('lgrs', {})
        super().__init__(*args, **kwargs)

        lgr_choices = sorted([((lgr_type, name), name) for lgr_type, names in lgrs.items() for name in names],
                             key=lambda x: x[1])

        for idn_table_name in idn_tables:
            self.fields[idn_table_name] = forms.ChoiceField(label=idn_table_name,
                                                            required=True,
                                                            choices=lgr_choices)
