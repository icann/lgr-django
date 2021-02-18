# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django import forms
from django.core import validators
from django.forms.widgets import Select, TextInput
from django.utils.six import iteritems
from django.utils.translation import ugettext_lazy as _

LGR_COMPARE_ACTIONS = (
    ("UNION", _("Union")),
    ("INTERSECTION", _("Intersection")),
    ("DIFF", _("Diff")))


class UAEmailValidator(validators.EmailValidator):
    # same Email Validator class with unicode characters instead of a-z0-9
    user_regex = validators._lazy_re_compile(r".+", re.IGNORECASE)
    domain_regex = validators._lazy_re_compile(r".+", re.IGNORECASE)


class UAEmailField(forms.EmailField):
    widget = TextInput
    default_validators = [UAEmailValidator()]


class DataSelectWidget(Select):
    """
    Add data to select widget options
    Data is a dict with key option value containing a dict of data name with data value
    """
    allow_multiple_selected = False

    def __init__(self, attrs=None, choices=(), data=None):
        super(DataSelectWidget, self).__init__(attrs)
        self.data = data

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        """
        Yield all "subwidgets" of this widget. Used to enable iterating
        options from a BoundField for choice widgets.
        """
        option = super(DataSelectWidget, self).create_option(name, value, label, selected, index, subindex, attrs)
        for key, val in iteritems(self.data.get(value, {})):
            # attrs won't be displayed if val is False and will be displayed without argument if val is True
            option['attrs']['data-{}'.format(key)] = val

        return option


class LGRCompareSelector(forms.Form):
    lgr_1 = forms.ChoiceField(label=_("First LGR"),
                              help_text=_('First LGR to use in tool'),
                              required=True,
                              widget=DataSelectWidget)

    lgr_2 = forms.ChoiceField(label=_("Second LGR"),
                              help_text=_('Second LGR to use in tool'),
                              required=True,
                              widget=DataSelectWidget)

    action = forms.ChoiceField(label=_("Action to perform on LGRs"),
                               help_text=_('Choose the action to perform on selected LGRs'),
                               required=True,
                               choices=LGR_COMPARE_ACTIONS,
                               initial="UNION")
    full_dump = forms.BooleanField(label=_("Full dump"),
                                   help_text=_('Print a full dump (i.e. with identical code points as well)'),
                                   required=False)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', [])
        super(LGRCompareSelector, self).__init__(*args, **kwargs)
        need_empty = False
        lgr_sets = [lgr for lgr in session_lgrs if lgr['is_set']]
        lgrs = [lgr for lgr in session_lgrs if not lgr['is_set']]
        if len(lgr_sets) < 2 or len(lgrs) < 2:
            need_empty = True

        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr_1'].choices = ((_('LGR'), [(lgr['name'], lgr['name']) for lgr in lgrs]),
                                        (_('LGR set'), [(lgr['name'], lgr['name']) for lgr in lgr_sets]))
        self.fields['lgr_2'].choices = ((lgr['name'], lgr['name']) for lgr in session_lgrs)
        self.fields['lgr_1'].widget.data = {lgr['name']: {'is-set': 'yes' if lgr['is_set'] else 'no'} for lgr in
                                            session_lgrs}
        self.fields['lgr_2'].widget.data = self.fields['lgr_1'].widget.data
        if need_empty:
            self.fields['lgr_2'].empty = True


class LGRDiffSelector(forms.Form):
    lgr_1 = forms.ChoiceField(label=_("First LGR"),
                              help_text=_('First LGR to use in tool'),
                              required=True)

    lgr_2 = forms.ChoiceField(label=_("Second LGR"),
                              help_text=_('Second LGR to use in tool'),
                              required=True)

    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in tool. '
                                         'File must be encoded in UTF-8 and using UNIX line ending.'),
                             required=True)

    email = UAEmailField(label=_("E-mail"),
                         help_text=_('Provide your e-mail address'),
                         required=True)

    collision = forms.BooleanField(label=_("Check collisions"),
                                   help_text=_('Also check for collision of '
                                               'labels in both LGR'),
                                   required=False)

    full_dump = forms.BooleanField(label=_("Full dump"),
                                   help_text=_('Print a full dump'),
                                   required=False)

    with_rules = forms.BooleanField(label=_("Output rules"),
                                    help_text=_('Show rules in output (this '
                                                'can be very verbose)'),
                                    required=False)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', [])
        super(LGRDiffSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        for lgr_f in ['lgr_1', 'lgr_2']:
            self.fields[lgr_f].choices = ((lgr['name'], lgr['name']) for lgr in session_lgrs if not lgr['is_set'])


class LGRCollisionSelector(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use in tool'),
                            required=True)

    download_tlds = forms.BooleanField(label=_("Also check for collision with existing TLDs"),
                                       required=False)

    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in tool. '
                                         'File must be encoded in UTF-8 and using UNIX line ending.'))

    email = UAEmailField(label=_("E-mail"),
                         help_text=_('Provide your e-mail address'),
                         required=True)

    full_dump = forms.BooleanField(label=_("Full dump"),
                                   help_text=_('Print a full dump'),
                                   required=False)

    with_rules = forms.BooleanField(label=_("Output rules"),
                                    help_text=_('Show rules in output (this '
                                                'can be very verbose)'),
                                    required=False)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', [])
        super(LGRCollisionSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((lgr['name'], lgr['name']) for lgr in session_lgrs if not lgr['is_set'])


class LGRSetCompatibleForm(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use in tool'),
                            required=True,
                            widget=DataSelectWidget)

    script = forms.ChoiceField(label=_("Script"),
                               help_text=_('The script used to validate the label'),
                               required=False)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', {})
        scripts = kwargs.pop('scripts', [])
        super(LGRSetCompatibleForm, self).__init__(*args, **kwargs)
        lgr_sets = [lgr for lgr in session_lgrs if lgr['is_set']]
        lgrs = [lgr for lgr in session_lgrs if not lgr['is_set']]
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((_('LGR'), [(lgr['name'], lgr['name']) for lgr in lgrs]),
                                      (_('LGR set'), [(lgr['name'], lgr['name']) for lgr in lgr_sets]))
        self.fields['lgr'].widget.data = {lgr['name']: {'lgr-set': ','.join([l['name'] for l in lgr['lgr_set_dct']])}
                                          for lgr in lgr_sets}

        if scripts:
            self.fields['script'].choices = scripts


class LGRAnnotateSelector(LGRSetCompatibleForm):
    set_labels = forms.FileField(label=_("Allocated Set labels"),
                                 required=False,
                                 help_text=_('Optional list of labels already allocated '
                                             'in the LGR set, that will be used to check '
                                             'for collisions when evaluating labels using '
                                             'the merged LGR set. '
                                             'File must be encoded in UTF-8 and using UNIX line ending.'))

    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in tool. '
                                         'File must be encoded in UTF-8 and using UNIX line ending.'),
                             required=True)

    email = UAEmailField(label=_("E-mail"),
                         help_text=_('Provide your e-mail address'),
                         required=True)


class LGRCrossScriptVariantsSelector(LGRSetCompatibleForm):
    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in tool. '
                                         'File must be encoded in UTF-8 and using UNIX line ending.'),
                             required=True)

    email = UAEmailField(label=_("E-mail"),
                         help_text=_('Provide your e-mail address'),
                         required=True)


class LGRHarmonizeSelector(forms.Form):
    lgr_1 = forms.ChoiceField(label=_('First LGR'),
                              help_text=_('First LGR to use in tool'),
                              required=True)

    lgr_2 = forms.ChoiceField(label=_('Second LGR'),
                              help_text=_('Second LGR to use in tool'),
                              required=True)

    rz_lgr = forms.ChoiceField(label=_('Root Zone LGR'),
                               help_text=_('The (optional) RootZone LGR to infer new variant sets from'),
                               required=False)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', {})
        super(LGRHarmonizeSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs
        for field_name in ('lgr_1', 'lgr_2', 'rz_lgr'):
            self.fields[field_name].choices = ((lgr['name'], lgr['name']) for lgr in session_lgrs if not lgr['is_set'])
        self.fields['rz_lgr'].choices = [('', ''), ] + self.fields['rz_lgr'].choices


class LGRComputeVariantsSelector(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use in tool'),
                            required=True)

    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in tool. '
                                         'File must be encoded in UTF-8 and using UNIX line ending.'))

    email = UAEmailField(label=_("E-mail"),
                         help_text=_('Provide your e-mail address'),
                         required=True)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', [])
        super(LGRComputeVariantsSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((lgr['name'], lgr['name']) for lgr in session_lgrs if not lgr['is_set'])
