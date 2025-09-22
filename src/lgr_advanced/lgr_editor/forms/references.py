import re

from django import forms
from django.forms.formsets import formset_factory
from django.utils.translation import gettext_lazy as _
from lgr.metadata import ReferenceManager

from lgr_advanced.lgr_editor.forms.utils import BaseDisableableFormSet, ReadOnlyTextInput


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

    def clean(self):
        cleaned_data = super(ReferenceForm, self).clean()
        if cleaned_data['ref_id'] and not re.match(ReferenceManager.REFERENCE_REGEX, str(cleaned_data['ref_id'])):
            self.add_error('ref_id', _('Invalid format'))

        return cleaned_data


ReferenceFormSet = formset_factory(ReferenceForm,
                                   formset=BaseDisableableFormSet,
                                   extra=0)
