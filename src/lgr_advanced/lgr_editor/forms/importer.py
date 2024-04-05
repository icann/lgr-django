# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core import validators
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _

from .fields import FILE_FIELD_ENCODING_HELP, ValidatingRepertoire


class NewLGRForm(forms.Form):
    validating_repertoire = forms.ChoiceField(label=_("Validating repertoire"),
                                              help_text=_('Code points will be limited to the selected repertoire'),
                                              required=False,
                                              choices=(('', ''),),
                                              initial=ValidatingRepertoire.default_choice())

    def __init__(self, *args, **kwargs):
        super(NewLGRForm, self).__init__(*args, **kwargs)
        self.fields['validating_repertoire'].choices = self.fields['validating_repertoire'].choices + list(
            ValidatingRepertoire.choices())


class CreateLGRForm(NewLGRForm):
    name = forms.CharField(label=_("Name"))

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False, field_order=None, use_required_attribute=None,
                 renderer=None):
        super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order,
                         use_required_attribute, renderer)


class ImportLGRForm(NewLGRForm):
    file = forms.FileField(label=_("Select file(s)"), required=True,
                           help_text=f"{_('If you select more than one file, this will create a LGR set.')} "
                                     f"{FILE_FIELD_ENCODING_HELP}",
                           widget=forms.ClearableFileInput(attrs={'multiple': True}))
    set_name = forms.CharField(label=_("LGR set name"),
                               required=False,
                               # TODO should catch that to get a valid LGR name
                               validators=[
                                   validators.RegexValidator(r'^[\w\_\-\.]+$',
                                                             _('Enter a valid LGR set name. '
                                                               'This value may contain only letters, numbers '
                                                               'and ./-/_ characters.'), 'invalid'),
                               ],
                               help_text=_('The name of the set'))
