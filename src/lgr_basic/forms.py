# -*- coding: utf-8 -*-
from dal import autocomplete
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import ugettext_lazy as _

from lgr.tools.utils import parse_label_input
from lgr_advanced.lgr_editor.forms.fields import LABEL_FILE_HELP, LABEL_INPUT_HELP
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_models.models.lgr import LgrBaseModel
from lgr_utils.unidb import get_db_by_version


class LgrGroupedListSelect2(autocomplete.ListSelect2):

    def filter_choices_to_render(self, selected_choices):
        # dal.widget.WidgetMixin.filter_choices_to_render does not handle correctly grouped lists
        # https://github.com/yourlabs/django-autocomplete-light/issues/1299
        ch = []
        for group in self.choices:
            c = [c for c in group[1] if str(c[0]) in selected_choices]
            ch.extend(c)
        self.choices = ch


class ValidateLabelSimpleForm(forms.Form):
    # The order of fields is important, it is tied to the order of the "clean_data" execution. Since clean_label uses
    # lgr, clean_lgr needs to execute before.
    lgr = autocomplete.Select2ListChoiceField(label='',
                                              required=True,
                                              widget=LgrGroupedListSelect2(url='ref-lgr-autocomplete',
                                                                           attrs={'data-allow-clear': 'false'}))

    labels = forms.CharField(label='', required=False, strip=False,
                             widget=forms.TextInput(attrs={'name': '',
                                                           'class': 'form-label form-control',
                                                           'onkeyup': 'buttonValidateEnabled()',
                                                           'placeholder': _('Label')}),
                             help_text=LABEL_INPUT_HELP)

    labels_file = forms.FileField(label='',
                                  help_text=LABEL_FILE_HELP,
                                  required=False,
                                  validators=[FileExtensionValidator(allowed_extensions=('', 'txt',))],
                                  widget=forms.FileInput(attrs={'accept': 'text/plain'}))
    collisions = forms.BooleanField(label='', widget=forms.CheckboxInput(attrs={'id': 'check-for-collision'}),
                                    required=False)

    include_mixed_script_variants = forms.BooleanField(label='',
                                                       widget=forms.CheckboxInput(
                                                           attrs={'id': 'hide-mixed-script-variants'}),
                                                       required=False)

    def __init__(self, *args, **kwargs):
        reflgr = kwargs.pop('reflgr')
        super(ValidateLabelSimpleForm, self).__init__(*args, **kwargs)
        self.fields['lgr'].choices = reflgr

    def clean(self):
        cleaned_data = super(ValidateLabelSimpleForm, self).clean()
        if 'labels' not in self.errors and not cleaned_data.get('labels') and not cleaned_data.get('labels_file'):
            self.add_error('labels', _('Required'))
            self.add_error('labels_file', _('Required'))

        if cleaned_data.get('labels') and cleaned_data.get('labels_file'):
            # should not happen
            self.add_error('labels', _('Unknown error, please report'))
            self.add_error('labels_file', _('Unknown error, please report'))

        return cleaned_data

    def clean_lgr(self):
        return LgrBaseModel.from_tuple(self.cleaned_data['lgr'])

    def clean_labels(self):
        udata = get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)
        value = self.cleaned_data['labels']
        labels = list()
        for label in {v: '' for v in value.split(';')}.keys():  # dict to remove duplicates but keep order
            if not label:
                continue
            labels.append(parse_label_input(label, idna_decoder=udata.idna_decode_label, keep_spaces=True))
        return labels
