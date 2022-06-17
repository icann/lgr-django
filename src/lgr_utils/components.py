from django.core.exceptions import ValidationError

from lgr_utils.views import RefLgrAutocomplete
from django import forms


class RefLgrAutocompleteField(forms.ChoiceField):
    def validate(self, value):
        found = False
        for lgr_types in RefLgrAutocomplete.get_list():
            for lgr in lgr_types[1]:
                if value == lgr[0]:
                    found = True
                    break;
        if not found:
            raise ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value},
            )
