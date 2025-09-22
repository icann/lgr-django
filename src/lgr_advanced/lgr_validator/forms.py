from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from lgr.tools.utils import parse_label_input

from lgr_advanced.lgr_editor.forms.fields import LABEL_INPUT_HELP
from lgr_advanced.lgr_exceptions import lgr_exception_to_text


class ValidateLabelForm(forms.Form):
    label = forms.CharField(label=_("Label"),
                            help_text=f'{LABEL_INPUT_HELP} {_("Maximum length: 63 code points")}')
    set_labels = forms.FileField(label=_("Allocated Set labels"),
                                 required=False,
                                 help_text=_('Optional list of labels already allocated '
                                             'in the LGR set, that will be used to check '
                                             'for collisions when evaluating labels using '
                                             'the merged LGR set'))
    script = forms.ChoiceField(label=_("Script"),
                               required=False,
                               help_text=_('The script used to validate the label'))
    include_mixed_script_variants = forms.BooleanField(label=_('Include mixed-script variants'),
                                                       widget=forms.CheckboxInput(),
                                                       required=False)

    def __init__(self, *args, **kwargs):
        self.idna_decoder = kwargs.pop('idna_decoder', None)
        scripts = kwargs.pop('scripts', None)
        super(ValidateLabelForm, self).__init__(*args, **kwargs)
        if scripts:
            self.fields['script'].choices = scripts
            self.fields['script'].required = True

    def clean_label(self):
        value = self.cleaned_data['label']
        kwargs = {}
        if self.idna_decoder:
            kwargs['idna_decoder'] = self.idna_decoder
        parsed_label, valid, ex = parse_label_input(value, **kwargs)
        if not valid:
            error = _('Invalid label')
            if ex:
                error = lgr_exception_to_text(ex)
            raise ValidationError(error)
        return parsed_label
