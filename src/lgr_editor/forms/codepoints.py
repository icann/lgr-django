# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.six import text_type
from django import forms

from lgr.tools.utils import parse_label_input, parse_single_cp_input, parse_codepoint_input
from .fields import (VALIDATING_REPERTOIRES,
                     DEFAULT_VALIDATING_REPERTOIRE)

SUPPORTED_CODEPOINT_INPUT_FILES = [
    ('rfc3743', 'RFC3743'),
    ('rfc4290', 'RFC4290'),
    ('one_per_line', 'One code point per line')
]


class CodepointField(forms.CharField):
    def __init__(self, *args, **kwargs):
        # single codepoint only?
        self.single = kwargs.pop('single', False)
        super(CodepointField, self).__init__(*args, **kwargs)

    def clean(self, value):
        """
        Validates the given value and returns its "cleaned" value as an
        appropriate Python object.

        Raises ValidationError for any errors.
        """

        # convert to python type and validate at the same time
        value = super(CodepointField, self).clean(value)
        try:
            if self.single:
                value = parse_single_cp_input(value)
            else:
                value = parse_codepoint_input(value)
        except ValueError as e:
            raise ValidationError(text_type(e))

        return value


class AddCodepointForm(forms.Form):
    codepoint = CodepointField(label=_("Code point"))
    override_repertoire = forms.BooleanField(label=_("Override repertoire"),
                                             required=False)


class AddMultiCodepointsForm(forms.Form):
    codepoint = forms.MultipleChoiceField(label=_('Code points'),
                                          widget=forms.CheckboxSelectMultiple(attrs={'checked': 'true'}))

    disabled_codepoint = forms.MultipleChoiceField(
        label=_('Disabled code points'),
        widget=forms.CheckboxSelectMultiple(attrs={'disabled': 'true'}))

    tmp_lgr = forms.CharField(widget=forms.HiddenInput, label='', initial=None)


class AddRangeForm(forms.Form):
    first_cp = CodepointField(label=_("First code point"), single=True)
    last_cp = CodepointField(label=_("Last code point"), single=True)

    def clean(self):
        cd = super(AddRangeForm, self).clean()
        # TODO check that we don't get sequences
        if 'first_cp' in cd and 'last_cp' in cd and cd['first_cp'] > cd['last_cp']:
            raise ValidationError(_('Last code point (%(last_cp)s) must not be '
                                    'smaller than the first code point '
                                    '(%(first_cp)s)') % cd)


class AddCodepointFromScriptForm(forms.Form):
    validating_repertoire = forms.ChoiceField(label=_("Validating repertoire"),
                                              required=True,
                                              choices=VALIDATING_REPERTOIRES,
                                              initial=DEFAULT_VALIDATING_REPERTOIRE)
    script = forms.ChoiceField(label=_("Script"),
                               required=True)
    manual_import = forms.BooleanField(label=_("Manual import"),
                                       required=False)

    def __init__(self, *args, **kwargs):
        super(AddCodepointFromScriptForm, self).__init__(*args, **kwargs)
        self.fields['script'].choices = self.initial['scripts']


class ImportCodepointsFromFileForm(forms.Form):
    file = forms.FileField(label=_("Select a file"))
    type = forms.ChoiceField(label=_("File type"),
                             choices=SUPPORTED_CODEPOINT_INPUT_FILES)
    manual_import = forms.BooleanField(label=_("Manual import"),
                                       required=False)


class AddVariantForm(forms.Form):
    codepoint = CodepointField(label=_("Code point"))
    override_repertoire = forms.BooleanField(label=_("Override repertoire"),
                                             required=False)


class ValidateLabelForm(forms.Form):
    label = forms.CharField(label=_("Label"))
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
        max_label_len = kwargs.pop('max_label_len', None)
        self.idna_decoder = kwargs.pop('idna_decoder', None)
        scripts = kwargs.pop('scripts', None)
        super(ValidateLabelForm, self).__init__(*args, **kwargs)
        if max_label_len is not None:
            self.fields['label'].help_text = _("Maximum length: %d code points" % max_label_len)
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


class MultipleChoiceFieldNoValidation(forms.MultipleChoiceField):

    def validate(self, value):
        # do not enable default validation as it will refuse our values as they are not in form choices
        # XXX we could validate that cp are in lgr
        pass


class EditCodepointsForm(forms.Form):
    when = forms.ChoiceField(label='when', required=False)
    not_when = forms.ChoiceField(label='not-when', required=False)
    tags = forms.CharField(label='Tags', required=False, help_text='space-separated tags')
    cp_id = MultipleChoiceFieldNoValidation()  # will contain a list of code points

    def __init__(self, post, *args, **kwargs):
        rule_names = kwargs.pop('rule_names', None)
        self.post = post
        super(EditCodepointsForm, self).__init__(post, *args, **kwargs)

        self.fields['when'].initial = None
        self.fields['not_when'].initial = None
        self.fields['tags'].initial = ''
        if rule_names:
            self.fields['when'].choices = rule_names
            self.fields['not_when'].choices = rule_names

    def clean(self):
        cleaned_data = super(EditCodepointsForm, self).clean()
        if self.post and 'add-rules' in self.post:
            if cleaned_data['when'] and cleaned_data['not_when']:
                self.add_error('when', 'Cannot add when and not-when rules simultaneously')
                self.add_error('not_when', 'Cannot add when and not-when rules simultaneously')
            elif not cleaned_data.get('when') and not cleaned_data.get('not_when'):
                self.add_error('when', 'Please provide at least one value')
                self.add_error('not_when', 'Please provide at least one value')

        if self.post and 'add-tags' in self.post and not cleaned_data.get('tags'):
            self.add_error('tags', 'Please provide at least one value')

        return cleaned_data
