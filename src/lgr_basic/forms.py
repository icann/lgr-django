# -*- coding: utf-8 -*-
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from lgr.tools.utils import parse_label_input
from lgr_advanced.lgr_editor.forms.fields import FILE_FIELD_ENCODING_HELP
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_models.exceptions import LGRUnsupportedUnicodeVersionException
from lgr_models.models.lgr import LgrBaseModel
from lgr_models.models.unicode import UnicodeVersion
from lgr_utils.unidb import get_db_by_version
from lgr_utils.views import RefLgrAutocomplete


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
                                              choice_list=RefLgrAutocomplete.get_list(),
                                              widget=LgrGroupedListSelect2(url='ref-lgr-autocomplete'))

    labels = forms.CharField(label='', required=False,
                             widget=forms.TextInput(attrs={'name': '',
                                                           'class': 'form-label form-control',
                                                           'onkeyup': 'buttonValidateEnabled()',
                                                           'placeholder': _('Label')}))

    labels_file = forms.FileField(label='', help_text=FILE_FIELD_ENCODING_HELP,
                                  required=False)
    collisions = forms.BooleanField(label='', widget=forms.CheckboxInput(attrs={'id': 'check-for-collision'}),
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
        lgr_object = self.cleaned_data['lgr']
        try:
            udata = get_db_by_version(lgr_object.to_lgr().metadata.unicode_version)
        except LGRUnsupportedUnicodeVersionException:
            # fallback to default version
            udata = get_db_by_version(UnicodeVersion.default().version)

        value = self.cleaned_data['labels']
        labels = list()
        for label in set(value.split(';')):
            if not label:
                continue
            try:
                labels.append(parse_label_input(label, idna_decoder=udata.idna_decode_label))
            except ValueError as e:
                raise ValidationError(lgr_exception_to_text(e))
        return labels
