# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from lgr.tools.utils import parse_single_cp_input, parse_codepoint_input
from lgr_advanced.lgr_editor.forms.fields import (ValidatingRepertoire,
                                                  FILE_FIELD_ENCODING_HELP)
from lgr_advanced.widgets import DataSelectWidget
from .utils import MultipleChoiceFieldNoValidation


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
            raise ValidationError(str(e))

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
                                              initial=ValidatingRepertoire.default_choice(),
                                              widget=DataSelectWidget)
    script = forms.ChoiceField(label=_("Script"),
                               required=True)
    manual_import = forms.BooleanField(label=_("Manual import"),
                                       required=False)

    def __init__(self, *args, **kwargs):
        unicode_database = kwargs.pop('unicode_database')
        scripts = ValidatingRepertoire.scripts(unicode_database)
        super(AddCodepointFromScriptForm, self).__init__(*args, **kwargs)
        self.fields['script'].choices = sorted(
            set((s, s) for vr_scripts in scripts.values() for s in vr_scripts))
        self.fields['validating_repertoire'].choices = ValidatingRepertoire.choices()
        self.fields['validating_repertoire'].widget.data = {
            k: {'scripts': ','.join(v)} for k, v in scripts.items()
        }


class ImportCodepointsFromFileForm(forms.Form):
    file = forms.FileField(label=_("Select a file"),
                           help_text=f"{_('File containing data to be imported.')} {FILE_FIELD_ENCODING_HELP}")
    manual_import = forms.BooleanField(label=_("Manual import"),
                                       required=False)


class AddVariantForm(forms.Form):
    codepoint = CodepointField(label=_("Code point"))
    override_repertoire = forms.BooleanField(label=_("Override repertoire"),
                                             required=False)


class EditCodepointsForm(forms.Form):
    when = forms.ChoiceField(label='when', required=False)
    not_when = forms.ChoiceField(label='not-when', required=False)
    tags = MultipleChoiceFieldNoValidation(label='Tags', required=False, help_text='space-separated tags')
    cp_id = MultipleChoiceFieldNoValidation()  # will contain a list of code points

    def __init__(self, *args, **kwargs):
        rule_names = kwargs.pop('rule_names', None)
        tags = kwargs.pop('tags', tuple())
        super(EditCodepointsForm, self).__init__(*args, **kwargs)
        if rule_names:
            self.fields['when'].choices = rule_names
            self.fields['not_when'].choices = rule_names
        self.fields['tags'].choices = tags

    def clean(self):
        cleaned_data = super(EditCodepointsForm, self).clean()
        if 'add-rules' in self.data:
            if cleaned_data['when'] and cleaned_data['not_when']:
                self.add_error('when', _('Cannot add when and not-when rules simultaneously'))
                self.add_error('not_when', _('Cannot add when and not-when rules simultaneously'))
            elif not cleaned_data.get('when') and not cleaned_data.get('not_when'):
                self.add_error('when', _('Please provide at least one value'))
                self.add_error('not_when', _('Please provide at least one value'))

        if 'add-tags' in self.data and not cleaned_data.get('tags'):
            self.add_error('tags', _('Please provide at least one value'))

        return cleaned_data
