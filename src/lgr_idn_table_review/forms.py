# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _


class LGRIdnTableReviewSelector(forms.Form):
    idn_table = forms.ChoiceField(label=_('IDN table'),
                                  required=True)

    ref_lgr = forms.ChoiceField(label=_('Ref. LGR'),
                                help_text=_('Second LGR to use in tool'),
                                required=True)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', {})
        lgr_id = kwargs.pop('lgr_id', '')
        super(LGRIdnTableReviewSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs
        for field_name in ('idn_table', 'ref_lgr'):
            self.fields[field_name].choices = ((name, name) for name in session_lgrs)
        self.fields['idn_table'].initial = lgr_id
