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
                               _(' You can select up to %(max_files)s IDN tables.') % {
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
        idn_tables = kwargs.pop('idn_tables', [])
        self.lgrs = kwargs.pop('lgrs', {})
        super().__init__(*args, **kwargs)

        for idn_table_name in idn_tables:
            self.fields[idn_table_name] = forms.ChoiceField(label=idn_table_name,
                                                            required=True,
                                                            choices=((lgr, lgr) for lgr in self.lgrs.keys()),
                                                            widget=autocomplete.ListSelect2(url='ref-lgr-autocomplete',
                                                                                            attrs={
                                                                                                'data-language': None
                                                                                            }))

    def clean(self):
        cleaned_data = super().clean()
        for field in cleaned_data:
            lgr_name = cleaned_data[field]
            # replace lgr value by a tuple (lgr_type, value), this is necessary as dal does not allow us to use values
            # different than display in choices. The next version should allow that (see commented part below)
            cleaned_data[field] = str((self.lgrs[lgr_name], lgr_name))
        return cleaned_data

# XXX Uncomment this and remove the old form when upgrading django-autocomplete-light to a version that
#     supports it (should be > 3.8.2) and that is working correctly
#     Check view as well to update RefLgrAutocomplete and remove lgrs from IdnTableReviewSelectReferenceView.get_form_kwargs
# class IdnTableReviewSelectReferenceForm(forms.Form):
#
#     def __init__(self, *args, **kwargs):
#         from lgr_idn_table_review.idn_tool.views import RefLgrAutocomplete
#
#         idn_tables = kwargs.pop('idn_tables', [])
#         super().__init__(*args, **kwargs)
#
#         for idn_table_name in idn_tables:
#             self.fields[idn_table_name] = forms.ChoiceField(label=idn_table_name,
#                                                             required=True,
#                                                             choices=RefLgrAutocomplete.get_list(),
#                                                             widget=autocomplete.ListSelect2(url='ref-lgr-autocomplete'))
