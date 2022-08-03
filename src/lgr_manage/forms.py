# -*- coding: utf-8 -*-
from dal import autocomplete
from django import forms
from django.forms import FileField, CharField
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_editor.forms import FILE_FIELD_ENCODING_HELP
from lgr_models.models.lgr import RzLgr, RzLgrMember, RefLgr, MSR, IDNARepertoire, RefLgrMember
from lgr_models.models.settings import LGRSettings
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
    repository = FileField(label=_("Reference LGR file(s)"), required=True,
                           help_text=FILE_FIELD_ENCODING_HELP,
                           widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = RefLgr
        fields = '__all__'
        labels = {
            'file': _('Common Reference LGR file'),
            'name': _('Name'),
        }

    def save(self, commit=True):
        ref_lgr = super(RefLgrCreateForm, self).save(commit=commit)
        for lgr in self.files.getlist('repository'):
            RefLgrMember.objects.create(file=lgr, name=lgr.name, ref_lgr=ref_lgr)
        return ref_lgr


class MSRCreateForm(forms.ModelForm):
    class Meta:
        model = MSR
        fields = '__all__'
        labels = {
            'file': _('MSR'),
            'name': _('Name'),
        }


class MSRIsActiveForm(forms.Form):
    active = forms.ModelChoiceField(label='', queryset=MSR.objects.all(), empty_label=None)


class IDNACreateForm(forms.ModelForm):
    class Meta:
        model = IDNARepertoire
        fields = '__all__'
        labels = {
            'file': _('IDNA Repertoire'),
            'name': _('Name'),
        }


class IDNAIsActiveForm(forms.Form):
    active = forms.ModelChoiceField(label='', queryset=IDNARepertoire.objects.all(), empty_label=None)


class RzLgrIsActiveForm(forms.Form):
    active = forms.ModelChoiceField(label='', queryset=RzLgr.objects.all(), empty_label=None)


class RefLgrIsActiveForm(forms.Form):
    active = forms.ModelChoiceField(label='', queryset=RefLgr.objects.all(), empty_label=None)


class LgrSettingsForm(forms.ModelForm):
    class Meta:
        model = LGRSettings
        fields = '__all__'
        labels = {
            'variant_calculation_limit': _('Variant Calculation Limit'),
            'variant_calculation_max': _('Variant Calculation Max'),
        }
        help_texts = {
            'variant_calculation_limit': _('Above this limit, only allocatable labels will be displayed and result '
                                           'can be downloaded'),
            'variant_calculation_max': _('Above this limit, results would be computed in a background task'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant_calculation_limit'].widget.attrs['min'] = 2
        self.fields['variant_calculation_max'].widget.attrs['min'] = 3
