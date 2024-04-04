# -*- coding: utf-8 -*-
from pathlib import Path

from dal import autocomplete
from django import forms
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.lgr_editor.forms import FILE_FIELD_ENCODING_HELP
from lgr_models.models.lgr import RzLgr, RzLgrMember, RefLgr, MSR, IDNARepertoire, RefLgrMember
from lgr_models.models.settings import LGRSettings
from lgr_utils.forms import MultipleFileField
from lgr_web.utils import IANA_LANG_REGISTRY


class RzLgrCreateForm(forms.ModelForm):
    repository = MultipleFileField(label=_("LGR file(s)"), required=True,
                                   help_text=FILE_FIELD_ENCODING_HELP)

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
            RzLgrMember.objects.create(file=lgr, name=lgr.name, common=rz_lgr)
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
        RefLgrMember.objects.create(common=self.ref_lgr, file=self.file, name=Path(self.file.name).stem,
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

    def clean(self):
        old_name = self.instance.name
        cleaned_data = super().clean()
        if 'file' not in self.changed_data:
            return cleaned_data
        self.instance.name = Path(self.cleaned_data['file'].name).stem
        if self.instance.name != old_name and RefLgrMember.objects.filter(common=self.instance.common,
                                                                          name=self.instance.name).exists():
            self.add_error('file', _('This reference LGR member already exists'))
        return cleaned_data


class RefLgrCreateForm(forms.ModelForm):
    members = MultipleFileField(label=_("Common Reference LGR member files"), required=True,
                                help_text=FILE_FIELD_ENCODING_HELP)

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
        self.ref_lgr_members = forms.modelformset_factory(RefLgrMember, form=RefLgrMemberCreateForm,
                                                          min_num=0, extra=0)(
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
        exclude = ['report_expiration_last_run']
        labels = {
            'variant_calculation_limit': _('Variant Calculation Limit'),
            'variant_calculation_max': _('Variant Calculation Max'),
            'variant_calculation_abort': _('Variant Calculation Skip'),
            'report_expiration_delay': _('Report expiration delay')
        }
        help_texts = {
            'variant_calculation_limit': _('Above this limit, only allocatable labels will be displayed and result '
                                           'can be downloaded'),
            'variant_calculation_max': _('Above this limit, results would be computed in a background task'),
            'variant_calculation_abort': _('Above this limit, no results would be computed'),
            'report_expiration_delay': _('The delay after which a report is automatically deleted, in days')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant_calculation_limit'].widget.attrs['min'] = 2
        self.fields['variant_calculation_max'].widget.attrs['min'] = 3
        self.fields['variant_calculation_abort'].widget.attrs['min'] = 4
