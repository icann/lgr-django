# -*- coding: utf-8 -*-
from dal import autocomplete
from django import forms
from django.utils.translation import ugettext_lazy as _
from multiupload.fields import MultiFileField

from lgr_advanced.lgr_editor.forms import IANA_LANG_REGISTRY
from lgr_auth.models import LgrUser
from lgr_idn_table_review.admin.models import RzLgr, RzLgrMember, RefLgr


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


class RefLgrCreateForm(forms.ModelForm):
    language_script = autocomplete.Select2ListChoiceField(label=_("Language/script tag"),
                                                          choice_list=[''] + sorted(IANA_LANG_REGISTRY),
                                                          widget=autocomplete.ListSelect2(url='language-autocomplete'),
                                                          initial='', required=True)

    class Meta:
        model = RefLgr
        fields = '__all__'
        labels = {
            'file': _('Reference LGR file'),
            'name': _('Name'),
        }
