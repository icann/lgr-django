# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from multiupload.fields import MultiFileField

from lgr_idn_table_review.admin.models import RzLgr, RzLgrMember


class RzLgrCreateForm(forms.ModelForm):
    repository = MultiFileField(label=_("LGR file(s)"), min_num=1,
                                help_text=_('File(s) must be encoded in UTF-8 and using UNIX line ending.'))

    class Meta:
        model = RzLgr
        fields = '__all__'
        labels = {
            'file': _('Common LGR file'),
            'name': _('Name')
        }

    def save(self, commit=True):
        rz_lgr = super(RzLgrCreateForm, self).save(commit=commit)
        for lgr in self.cleaned_data['repository']:
            RzLgrMember.objects.create(file=lgr, name=lgr.name, rz_lgr=rz_lgr)
        return rz_lgr
