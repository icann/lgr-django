# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from multiupload.fields import MultiFileField


class LGRIdnTableReviewForm(forms.Form):
    idn_tables = MultiFileField(label=_('Select IDN table(s) to review'), min_num=1, max_num=20,
                                help_text=_('File(s) must be encoded in UTF-8 and using UNIX line ending.'
                                            'You can select up to 20 IDN tables.'))


class IdnTableReviewSelectReferenceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        idn_tables = kwargs.pop('idn_tables', [])
        ref_lgrs = kwargs.pop('ref_lgrs', [])
        super().__init__(*args, **kwargs)
        for idn_table_name in idn_tables:
            self.fields[idn_table_name] = forms.ChoiceField(label=idn_table_name,
                                                            required=True,
                                                            choices=[(ref, ref) for ref in ref_lgrs])
