# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.formsets import formset_factory

from .utils import BaseDisableableFormSet, ReadOnlyTextInput


class ReferenceForm(forms.Form):
    # Keep reference id
    # Not required since this form is also used to create new references
    ref_id = forms.CharField(label='', required=False)

    # Editable fields
    description = forms.CharField(label='')
    comment = forms.CharField(label='', required=False)

    def __init__(self, *args, **kwargs):
        ro_id = kwargs.pop('ro_id', True)
        super(ReferenceForm, self).__init__(*args, **kwargs)

        if ro_id:
            self.fields['ref_id'].widget = ReadOnlyTextInput()


ReferenceFormSet = formset_factory(ReferenceForm,
                                   formset=BaseDisableableFormSet,
                                   extra=0)
