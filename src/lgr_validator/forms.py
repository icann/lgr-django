# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.six import text_type
from django import forms

from lgr.tools.utils import parse_label_input
from lgr_editor.forms.fields import ROOT_ZONES
from lgr_tools.forms import UAEmailField


class ValidateLabelForm(forms.Form):
    label = forms.CharField(label=_("Label"),
                            help_text=_("Maximum length: 63 code points"))
    email = UAEmailField(label=_("E-mail"),
                         help_text=_('Provide your e-mail address'),
                         required=False)
    set_labels = forms.FileField(label=_("Allocated Set labels"),
                                 required=False,
                                 help_text=_('Optional list of labels already allocated '
                                             'in the LGR set, that will be used to check '
                                             'for collisions when evaluating labels using '
                                             'the merged LGR set'))
    script = forms.ChoiceField(label=_("Script"),
                               required=False,
                               help_text=_('The script used to validate the label'))

    def __init__(self, *args, **kwargs):
        lgr_info = kwargs.pop('lgr_info', None)
        self.idna_decoder = kwargs.pop('idna_decoder', None)
        scripts = kwargs.pop('scripts', None)
        super(ValidateLabelForm, self).__init__(*args, **kwargs)
        if scripts:
            self.fields['script'].choices = scripts
            self.fields['script'].required = True
        if lgr_info is not None and lgr_info.set_labels_info is not None:
            self.fields['set_labels'].initial = lgr_info.set_labels_info.name

    def clean_label(self):
        value = self.cleaned_data['label']
        kwargs = {}
        if self.idna_decoder:
            kwargs['idna_decoder'] = self.idna_decoder
        try:
            value = parse_label_input(value, **kwargs)
        except ValueError as e:
            raise ValidationError(text_type(e))
        return value


class ValidateLabelSimpleForm(forms.Form):
    rz_lgr = forms.ChoiceField(required=True, choices=ROOT_ZONES)
    labels = forms.CharField(required=False)
    labels_file = forms.FileField(help_text=_('File must be encoded in UTF-8 and using UNIX line ending.'),
                                  required=False)
    email = UAEmailField(label=_("E-mail"), required=False,
                         help_text=_("As the computing may be very long, we will warn by e-mail once the result can "
                                     "be downloaded."))
    collisions = forms.BooleanField(label=_("Check for collisions"),
                                    required=False)

    def clean(self):
        cleaned_data = super(ValidateLabelSimpleForm, self).clean()
        if self.cleaned_data.get('collisions'):
            if not self.cleaned_data.get('email'):
                self.add_error('email', _('E-mail is mandatory to get the collision test results'))

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
