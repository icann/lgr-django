# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from lgr_models.models.lgr import RzLgr
from .fields import (DEFAULT_UNICODE_VERSION,
                     FILE_FIELD_ENCODING_HELP)


class NewLGRForm(forms.Form):
    #  TODO:  we need to add the other repertoires (and not just the root zone one) as well here:
    validating_repertoire = forms.ModelChoiceField(queryset=RzLgr.objects.all(), required=False)


class CreateLGRForm(NewLGRForm):
    name = forms.CharField(label=_("Name"))
    unicode_version = forms.CharField(widget=forms.HiddenInput(),
                                      initial=DEFAULT_UNICODE_VERSION)


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
