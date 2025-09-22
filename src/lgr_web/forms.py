from django import forms
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from lgr.tools.utils import parse_label_input

from lgr_advanced.lgr_editor.forms.fields import LABEL_FILE_HELP, LABEL_INPUT_HELP
from lgr_utils import unidb


class LabelFormsForm(forms.Form):
    label = forms.CharField(label=_("Label"),
                            help_text=LABEL_INPUT_HELP)

    def clean(self):
        label = self.cleaned_data['label']
        udata = unidb.manager.get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)
        self.cleaned_data['label'], _, _ = parse_label_input(label, idna_decoder=udata.idna_decode_label,
                                                             keep_spaces=True)

        return self.cleaned_data


class LabelFileFormsForm(forms.Form):
    labels = forms.FileField(label=_("Labels"),
                             help_text=LABEL_FILE_HELP,
                             required=True,
                             validators=[FileExtensionValidator(allowed_extensions=('', 'txt',))],
                             widget=forms.FileInput(attrs={'accept': 'text/plain'}))
