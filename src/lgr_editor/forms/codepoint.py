# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import partial
from urllib import quote_plus

from django import forms
from django.forms.formsets import BaseFormSet, formset_factory
from django.utils.translation import ugettext_lazy as _


ReadOnlyTextInput = partial(forms.TextInput, {'readonly': 'readonly'})


class CodepointForm(forms.Form):
    when = forms.ChoiceField(label=_('When'), required=False)
    not_when = forms.ChoiceField(label=_('Not-When'), required=False)
    tags = forms.CharField(required=False, label=_('Tags'), help_text=_('space-separated tags'))
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': '2'}))

    def __init__(self, *args, **kwargs):
        rule_names = kwargs.pop('rules', tuple())
        super(CodepointForm, self).__init__(*args, **kwargs)

        self.fields['when'].choices = rule_names
        self.fields['not_when'].choices = rule_names


class CodepointVariantForm(forms.Form):
    # Keep codepoint slug
    cp = forms.CharField(widget=forms.HiddenInput, label='')

    # Display fields (read-only)
    cp_disp = forms.CharField(required=False, label='',
                              widget=ReadOnlyTextInput())
    name = forms.CharField(required=False, label='', widget=ReadOnlyTextInput())
    age = forms.CharField(required=False, label='', widget=ReadOnlyTextInput())
    when = forms.ChoiceField(label='', required=False)
    not_when = forms.ChoiceField(label='', required=False)
    references = forms.CharField(required=False, label='',
                                 widget=ReadOnlyTextInput())

    # Editable fields
    type = forms.CharField(label='')
    comment = forms.CharField(label='', required=False, widget=forms.Textarea(attrs={'rows': '2',
                                                                                     'cols': '30',
                                                                                     'class': 'form-control'}))

    def to_slug(self):
        return '{},{},{}'.format(
            self['cp'].value(),
            quote_plus(self['when'].value() or ''),
            quote_plus(self['not_when'].value() or '')
        )

    def reference_list(self):
        return filter(None, self['references'].value())


class BaseCodepointVariantFormSet(BaseFormSet):
    """
    Custom FormSet implementation to be able to dynamically set the choices
    of the encapsulated form.
    """

    def __init__(self, *args, **kwargs):
        self.rule_names = kwargs.pop('rules', tuple())
        super(BaseCodepointVariantFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        """
        Called when building "internal" forms.

        Hook ourselves into this function to set the "when"
        and "not-when" fields' choices.
        """
        form = super(BaseCodepointVariantFormSet, self)._construct_form(i,
                                                                        **kwargs)
        form.fields['when'].choices = self.rule_names
        form.fields['not_when'].choices = self.rule_names
        return form


CodepointVariantFormSet = formset_factory(CodepointVariantForm,
                                          formset=BaseCodepointVariantFormSet,
                                          extra=0)
