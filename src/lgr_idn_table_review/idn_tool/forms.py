# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from dal import autocomplete
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import FileField
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_editor.forms import FILE_FIELD_ENCODING_HELP


class LGRIdnTableReviewForm(forms.Form):
    idn_tables = FileField(label=_('Select IDN table(s) to review'),
                           help_text="%s %s" % (
                               FILE_FIELD_ENCODING_HELP,
                               _('You can select up to %(max_files)s IDN tables.') % {
                                   'max_files': settings.MAX_USER_IDN_REVIEW_INPUT}),
                           required=True,
                           widget=forms.ClearableFileInput(attrs={'multiple': True}))

    def clean_idn_tables(self):
        if len(self.files.getlist('idn_tables')) > settings.MAX_USER_IDN_REVIEW_INPUT:
            raise ValidationError(_('You can upload up to %(max_files)s files') % {
                'max_files': settings.MAX_USER_IDN_REVIEW_INPUT})
        return self.cleaned_data['idn_tables']


class IdnTableReviewSelectReferenceForm(forms.Form):

    def __init__(self, *args, **kwargs):
        from lgr_utils.views import RefLgrAutocompleteWithCore

        idn_tables = kwargs.pop('idn_tables', [])
        super().__init__(*args, **kwargs)

        for idn_table in idn_tables:
            self.fields[str(idn_table.pk)] = forms.ChoiceField(label=idn_table.name,
                                                               required=False,
                                                               choices=RefLgrAutocompleteWithCore.get_list(),
                                                               widget=autocomplete.ListSelect2(
                                                                   url='ref-lgr-autocomplete-with-core'))
            self.fields['file_' + str(idn_table.pk)] = FileField(label=idn_table.name,
                                                                 required=False,
                                                                 widget=forms.ClearableFileInput(
                                                                     attrs={'multiple': False}))

    def clean(self):
        cleaned_data = super(IdnTableReviewSelectReferenceForm, self).clean()
        new_cleaned_data = {}
        for name, value in cleaned_data.items():
            if 'file_' not in name:
                filename = f'file_{name}'
                if value == '':
                    if cleaned_data[filename] is not None:
                        new_cleaned_data[name] = cleaned_data[filename]
                    else:
                        self.add_error(name, _("Required"))
                        self.add_error(filename, _("Required"))
                else:
                    new_cleaned_data[name] = value

        return new_cleaned_data
