# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from lgr_models.models import RzLgr
from .fields import (DEFAULT_UNICODE_VERSION,
                     VALIDATING_REPERTOIRES,
                     DEFAULT_VALIDATING_REPERTOIRE,
                     FILE_FIELD_ENCODING_HELP)


class CreateLGRForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    validating_repertoire = forms.ChoiceField(label=_("Validating repertoire"),
                                              help_text=_('Code points will be limited to the selected repertoire'),
                                              required=False,
                                              choices=(('', ''),) + VALIDATING_REPERTOIRES,
                                              initial=DEFAULT_VALIDATING_REPERTOIRE)
    unicode_version = forms.CharField(widget=forms.HiddenInput(),
                                      initial=DEFAULT_UNICODE_VERSION)


class ImportLGRForm(forms.Form):
    file = forms.FileField(label=_("Select file(s)"), required=True,
                           help_text=f"{_('If you select more than one file, this will create a LGR set.')} "
                                     f"{FILE_FIELD_ENCODING_HELP}",
                           widget=forms.ClearableFileInput(attrs={'multiple': True}))
    #  TODO:  we need to add the other repertoires (and not just the root zone one) as well here:
    validating_repertoire = forms.ModelChoiceField(queryset=RzLgr.objects.all(), empty_label=None, to_field_name='name')
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
