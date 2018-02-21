# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.widgets import Select
from django.utils.translation import ugettext_lazy as _

LGR_COMPARE_ACTIONS = (
    ("UNION", _("Union")),
    ("INTERSECTION", _("Intersection")),
    ("DIFF", _("Diff")))


class DataSelectWidget(Select):
    """
    Add data to select widget options
    Data is a dict with key option value containing a dict of data name with data value
    """
    allow_multiple_selected = False

    def __init__(self, attrs=None, choices=(), data=None):
        super(DataSelectWidget, self).__init__(attrs)
        self.data = data

    def render_option(self, selected_choices, option_value, option_label):
        option = super(DataSelectWidget, self).render_option(selected_choices, option_value, option_label)
        str_data = ''
        for key, val in self.data.get(option_value, {}).iteritems():
            str_data += 'data-%s="%s" ' % (key, val)
        return option.replace("value=", str_data + "value=")  # XXX is there a better way without rewriting all method from scratch


class LGRCompareSelector(forms.Form):
    lgr_1 = forms.ChoiceField(label=_("First LGR"),
                              help_text=_('First LGR to use in comparison'),
                              required=True,
                              widget=DataSelectWidget)

    lgr_2 = forms.ChoiceField(label=_("Second LGR"),
                              help_text=_('Second LGR to use in comparison'),
                              required=True,
                              widget=DataSelectWidget)

    action = forms.ChoiceField(label=_("Action to perform on LGRs"),
                               help_text=_('Choose the action to perform on selected LGRs'),
                               required=True,
                               choices=LGR_COMPARE_ACTIONS,
                               initial="UNION")

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', [])
        lgr_id = kwargs.pop('lgr_id', '')
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
        self.fields['lgr_1'].widget.data = {lgr['name']: {'is-set': lgr['is_set']} for lgr in session_lgrs}
        self.fields['lgr_2'].widget.data = self.fields['lgr_1'].widget.data
        if need_empty:
            self.fields['lgr_2'].empty = True
        self.fields['lgr_1'].initial = lgr_id


class LGRDiffSelector(forms.Form):
    lgr_1 = forms.ChoiceField(label=_("First LGR"),
                              help_text=_('First LGR to use in diff'),
                              required=True)

    lgr_2 = forms.ChoiceField(label=_("Second LGR"),
                              help_text=_('Second LGR to use in diff'),
                              required=True)

    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in diff. '
                                         'File must be encoded in UNIX format.'),
                             required=True)

    email = forms.EmailField(label=_("E-mail"),
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
        lgr_id = kwargs.pop('lgr_id', '')
        super(LGRDiffSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        for lgr_f in ['lgr_1', 'lgr_2']:
            self.fields[lgr_f].choices = ((name, name) for name in session_lgrs)
        self.fields['lgr_1'].initial = lgr_id


class LGRCollisionSelector(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use for collisions'),
                            required=True)

    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in diff. '
                                         'File must be encoded in UNIX format.'),
                             required=True)

    email = forms.EmailField(label=_("E-mail"),
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
        lgr_id = kwargs.pop('lgr_id', '')
        super(LGRCollisionSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((name, name) for name in session_lgrs)
        self.fields['lgr'].initial = lgr_id


class LGRSetCompatibleForm(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use for annotation'),
                            required=True,
                            widget=DataSelectWidget)

    script = forms.ChoiceField(label=_("Script"),
                               help_text=_('The script used to validate the label'),
                               required=False)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', {})
        lgr_id = kwargs.pop('lgr_id', '')
        lgr_info = kwargs.pop('lgr_info', None)
        scripts = kwargs.pop('scripts', [])
        super(LGRSetCompatibleForm, self).__init__(*args, **kwargs)
        lgr_sets = [lgr for lgr in session_lgrs if lgr['is_set']]
        lgrs = [lgr for lgr in session_lgrs if not lgr['is_set']]
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((_('LGR'), [(lgr['name'], lgr['name']) for lgr in lgrs]),
                                      (_('LGR set'), [(lgr['name'], lgr['name']) for lgr in lgr_sets]))
        self.fields['lgr'].widget.data = {lgr['name']: {'lgr-set': ','.join([l['name'] for l in lgr['lgr_set_dct']])}
                                          for lgr in lgr_sets}
        self.fields['lgr'].initial = lgr_id
        if lgr_info is not None:
            self.fields['lgr'].initial = lgr_info.name

        if scripts:
            self.fields['script'].choices = scripts


class LGRAnnotateSelector(LGRSetCompatibleForm):
    set_labels = forms.FileField(label=_("Allocated Set labels"),
                                 required=False,
                                 help_text=_('Optional list of labels already allocated '
                                             'in the LGR set, that will be used to check '
                                             'for collisions when evaluating labels using '
                                             'the merged LGR set'))

    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in diff. '
                                         'File must be encoded in UNIX format.'),
                             required=True)

    email = forms.EmailField(label=_("E-mail"),
                             help_text=_('Provide your e-mail address'),
                             required=True)

    def __init__(self, *args, **kwargs):
        lgr_info = kwargs.get('lgr_info', None)
        super(LGRAnnotateSelector, self).__init__(*args, **kwargs)
        if lgr_info is not None and lgr_info.set_labels_info is not None:
            self.fields['set_labels'].initial = lgr_info.set_labels_info.name


class LGRCrossScriptVariantsSelector(LGRSetCompatibleForm):
    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in diff. '
                                         'File must be encoded in UNIX format.'),
                             required=True)

    email = forms.EmailField(label=_("E-mail"),
                             help_text=_('Provide your e-mail address'),
                             required=True)


class LGRCheckHarmonizedSelector(forms.Form):
    lgrs = forms.MultipleChoiceField(label=_("LGRs"),
                                     help_text=_('LGRs to use for harmonization check'),
                                     required=True)

    email = forms.EmailField(label=_("E-mail"),
                             help_text=_('Provide your e-mail address'),
                             required=True)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', {})
        lgr_id = kwargs.pop('lgr_id', '')
        super(LGRCheckHarmonizedSelector, self).__init__(*args, **kwargs)
        lgr_sets = [lgr for lgr in session_lgrs if lgr['is_set']]
        lgrs = [lgr for lgr in session_lgrs if not lgr['is_set']]
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgrs'].choices = ((_('LGR'), [(lgr['name'], lgr['name']) for lgr in lgrs]),
                                       (_('LGR set'), [(lgr['name'], lgr['name']) for lgr in lgr_sets]))
        self.fields['lgrs'].widget.data = {lgr['name']: {'lgr-set': ','.join([l['name'] for l in lgr['lgr_set_dct']])}
                                           for lgr in lgr_sets}
        self.fields['lgrs'].initial = lgr_id