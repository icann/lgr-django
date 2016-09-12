# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import partial

from django import forms
from django.forms.formsets import formset_factory

ReadOnlyTextInput = partial(forms.TextInput, {'readonly': 'readonly'})


class ReferenceForm(forms.Form):
    # Keep reference id
    # Not required since this form is also used to create new references
    ref_id = forms.CharField(label='', required=False,
                             widget=ReadOnlyTextInput())

    # Editable fields
    description = forms.CharField(label='')
    comment = forms.CharField(label='', required=False)


ReferenceFormSet = formset_factory(ReferenceForm, extra=0)
