# -*- coding: utf-8 -*-
from pathlib import Path

from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_editor.forms import FILE_FIELD_ENCODING_HELP
from lgr_models.models.lgr import RzLgr, RzLgrMember, RefLgr, MSR, IDNARepertoire, RefLgrMember
from lgr_models.models.settings import LGRSettings
from lgr_web.utils import IANA_LANG_REGISTRY


class RzLgrCreateForm(forms.ModelForm):
    repository = forms.FileField(label=_("LGR file(s)"), required=True,
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
            RzLgrMember.objects.create(file=lgr, name=f'{rz_lgr.name}-{lgr.name}', rz_lgr=rz_lgr)
        return rz_lgr


class RefLgrMemberCreateForm(forms.ModelForm):
    file_name = forms.CharField(label=_("Reference LGR member file"),
                                disabled=True)
    language_script = autocomplete.Select2ListCreateChoiceField(label=_("Language/script tag"),
                                                                choice_list=[''] + sorted(IANA_LANG_REGISTRY),
                                                                widget=autocomplete.ListSelect2(
                                                                    url='language-autocomplete'),
                                                                initial='', required=True)

    class Meta:
        model = RefLgrMember
        fields = ['language_script']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file = None
        self.ref_lgr = None

    def full_clean(self):
        self.fields['file_name'].disabled = False  # allow setting file_name
        return super().full_clean()

    def clean(self):
        filename = self.cleaned_data['file_name']
        for file in self.files.getlist('members'):
            if filename == file.name:
                self.file = file
                break
        else:
            self.add_error('file_name', _('Unable to retrieve file with this name'))
        return self.cleaned_data

    def save(self, commit=True):
        name = f"{self.ref_lgr.name}-{Path(self.file.name).stem}"
        RefLgrMember.objects.create(ref_lgr=self.ref_lgr, file=self.file, name=name,
                                    language_script=self.cleaned_data['language_script'])


class RefLgrMemberUpdateForm(forms.ModelForm):
    file = forms.FileField(label=_("Reference LGR member file"), required=True,
                           help_text=FILE_FIELD_ENCODING_HELP,
                           widget=forms.ClearableFileInput())
    language_script = autocomplete.Select2ListCreateChoiceField(label=_("Language/script tag"),
                                                                choice_list=[''] + sorted(IANA_LANG_REGISTRY),
                                                                widget=autocomplete.ListSelect2(
                                                                    url='language-autocomplete'),
                                                                required=True)

    class Meta:
        model = RefLgrMember
        fields = ['file', 'language_script']


class RefLgrCreateForm(forms.ModelForm):
    members = forms.FileField(label=_("Common Reference LGR member files"), required=True,
                              help_text=FILE_FIELD_ENCODING_HELP,
                              widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = RefLgr
        fields = ['name', 'file']
        labels = {
            'name': _('Name'),
            'file': _('Common Reference LGR file'),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('instance', None)
        super(RefLgrCreateForm, self).__init__(*args, **kwargs)
        self.ref_lgr_members = forms.modelformset_factory(RefLgrMember, form=RefLgrMemberCreateForm, min_num=0, extra=0)(
            *args, **kwargs, queryset=RefLgrMember.objects.none())

    def _clean_fields(self):
        if 'id' in self.fields:
            self.fields['id'].required = False
        super(RefLgrCreateForm, self)._clean_fields()

    def clean(self):
        super(RefLgrCreateForm, self).clean()
        if not self.ref_lgr_members.is_valid():
            self.add_error('members', 'Invalid members data')
        self.ref_lgr_members.clean()
        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        ref_lgr = super(RefLgrCreateForm, self).save(commit=commit)
        for member in self.ref_lgr_members:
            member.ref_lgr = ref_lgr
            member.save()
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
            'variant_calculation_abort': _('Variant Calculation Skip'),
        }
        help_texts = {
            'variant_calculation_limit': _('Above this limit, only allocatable labels will be displayed and result '
                                           'can be downloaded'),
            'variant_calculation_max': _('Above this limit, results would be computed in a background task'),
            'variant_calculation_abort': _('Above this limit, no results would be computed'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant_calculation_limit'].widget.attrs['min'] = 2
        self.fields['variant_calculation_max'].widget.attrs['min'] = 3
        self.fields['variant_calculation_abort'].widget.attrs['min'] = 4
