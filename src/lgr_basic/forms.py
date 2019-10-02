# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.utils.six import text_type
from django.utils.translation import ugettext_lazy as _

from lgr.tools.utils import parse_label_input
from lgr_editor.forms.fields import ROOT_ZONES
from lgr_tools.forms import UAEmailField


class ValidateLabelSimpleForm(forms.Form):
    rz_lgr = forms.ChoiceField(label='', required=True, choices=ROOT_ZONES, initial=ROOT_ZONES[-1][0])
    labels = forms.CharField(label='', required=False,
                             widget=forms.TextInput(attrs={'name': '',
                                                           'class': 'form-label form-control',
                                                           'onkeyup': 'buttonValidateEnabled()',
                                                           'placeholder': _('Label')}))
    labels_file = forms.FileField(label='', help_text=_('File must be encoded in UTF-8 and using UNIX line ending.'),
                                  required=False)
    email = UAEmailField(label='', required=False,
                         widget=forms.TextInput(attrs={'id': 'email-task',
                                                       'placeholder': _('Email address for tasks results')}),
                         help_text=_("As the computing may be very long, we will warn by e-mail once the result can "
                                     "be downloaded."))
    collisions = forms.BooleanField(label='', widget=forms.CheckboxInput(attrs={'id': 'check-for-collision'}),
                                    required=False)

    def clean(self):
        cleaned_data = super(ValidateLabelSimpleForm, self).clean()
        if self.cleaned_data.get('collisions') or self.cleaned_data.get('labels_file'):
            if not self.cleaned_data.get('email'):
                self.add_error('email', _('E-mail is mandatory to get the tasks results'))

        if not cleaned_data.get('labels') and not cleaned_data.get('labels_file'):
            self.add_error('labels', _('Required'))
            self.add_error('labels_file', _('Required'))

        if cleaned_data.get('labels') and cleaned_data.get('labels_file'):
            # should not happen
            self.add_error('labels', _('Unknown error, please report'))
            self.add_error('labels_file', _('Unknown error, please report'))

        return cleaned_data

    def clean_labels(self):
        value = self.cleaned_data['labels']
        labels = list()
        for label in set(value.split(';')):
            if not label:
                continue
            try:
                labels.append(parse_label_input(label))
            except ValueError as e:
                raise ValidationError(text_type(e))
        return labels
