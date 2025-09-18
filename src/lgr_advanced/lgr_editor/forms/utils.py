# -*- coding: utf-8 -*-
from functools import partial

from django import forms


ReadOnlyTextInput = partial(forms.TextInput, {'readonly': 'readonly'})


class BaseDisableableFormSet(forms.formsets.BaseFormSet):
    """
    Custom FormSet implementation to be able to dynamically set disabled flag on inputs
    """

    def __init__(self, *args, **kwargs):
        self.disabled = kwargs.pop('disabled', False)
        super(BaseDisableableFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        """
        Called when building "internal" forms.

        Hook ourselves into this function to set the required flag on fields
        """
        form = super(BaseDisableableFormSet, self)._construct_form(i, **kwargs)

        if self.disabled:
            for field in form.fields.values():
                field.disabled = True

        return form


class MultipleChoiceFieldNoValidation(forms.MultipleChoiceField):

    def validate(self, value):
        # do not enable default validation as it will refuse our values as they are not in form choices
        # XXX we could perform some validation though
        #  - validate that cp are in lgr
        #  - validate the tag format is correct
        pass
