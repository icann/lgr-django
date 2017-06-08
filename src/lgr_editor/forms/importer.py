# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core import validators
from multiupload.fields import MultiFileField
from .fields import (DEFAULT_UNICODE_VERSION,
                     VALIDATING_REPERTOIRES,
                     DEFAULT_VALIDATING_REPERTOIRE)


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
    file = MultiFileField(label=_("Select file(s)"), min_num=1,
                          help_text='If you select more than one file, this will create a LGR set')
    # TODO if more than one file: add forms.CharField LGR set name
    validating_repertoire = forms.ChoiceField(label=_("Validating repertoire"),
                                              help_text=_('Code points will be limited to the selected repertoire'),
                                              required=False,
                                              choices=(('', ''),) + VALIDATING_REPERTOIRES,
                                              initial=DEFAULT_VALIDATING_REPERTOIRE)
    set_name = forms.CharField(label=_("LGR set name"),
                               required=False,
                               # TODO should catch that to get a valid LGR name
                               validators=[
                                   validators.RegexValidator(r'^[\w\_\-\.]+$',
                                                             _('Enter a valid LGR set name. '
                                                               'This value may contain only letters, numbers '
                                                               'and ./-/_ characters.'), 'invalid'),
                               ],
                               help_text=_('The name of the label set'),
                               )
    set_labels = forms.FileField(label=_("Optional set labels"),
                                 required=False,
                                 help_text=_('Labels existing in the LGR set, '
                                             'that will be used to check for collisions '
                                             'when evaluating labels on the LGR set'))
