# -*- coding: utf-8 -*-
from dal import autocomplete
from django import forms
from django.forms import FileField
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_editor.forms import FILE_FIELD_ENCODING_HELP
from lgr_auth.models import LgrUser
from lgr_idn_table_review.idn_admin.models import RzLgr, RzLgrMember, RefLgr
from lgr_web.utils import IANA_LANG_REGISTRY


class RzLgrCreateForm(forms.ModelForm):
    repository = FileField(label=_("LGR file(s)"), required=True,
                           help_text=FILE_FIELD_ENCODING_HELP,
                           widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = RzLgr
        fields = '__all__'
        labels = {
            'file': _('Common LGR file'),
            'name': _('Name')
        }

    def save(self, commit=True):
        rz_lgr = super(RzLgrCreateForm, self).save(commit=commit)
        for lgr in self.files.getlist('repository'):
            RzLgrMember.objects.create(file=lgr, name=lgr.name, rz_lgr=rz_lgr)
        return rz_lgr


class RefLgrCreateForm(forms.ModelForm):
    language_script = autocomplete.Select2ListCreateChoiceField(label=_("Language/script tag"),
                                                                choice_list=[''] + sorted(IANA_LANG_REGISTRY),
                                                                widget=autocomplete.ListSelect2(
                                                                    url='language-autocomplete'),
                                                                initial='', required=True)

    class Meta:
        model = RefLgr
        fields = '__all__'
        labels = {
            'file': _('Reference LGR file'),
            'name': _('Name'),
        }


class UserCreateForm(forms.ModelForm):
    class Meta:
        model = LgrUser
        fields = ['email']
