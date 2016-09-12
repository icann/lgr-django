# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

LGR_COMPARE_ACTIONS = (
    ("UNION", _("Union")),
    ("INTERSECTION", _("Intersection")),
    ("DIFF", _("Diff")))


class LGRCompareSelector(forms.Form):
    lgr_1 = forms.ChoiceField(label=_("First LGR"),
                              help_text=_('First LGR to use in comparison'),
                              required=True)

    lgr_2 = forms.ChoiceField(label=_("Second LGR"),
                              help_text=_('Second LGR to use in comparison'),
                              required=True)

    action = forms.ChoiceField(label=_("Action to perform on LGRs"),
                               help_text=_('Choose the action to perform on selected LGRs'),
                               required=True,
                               choices=LGR_COMPARE_ACTIONS,
                               initial="UNION")

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', [])
        lgr_id = kwargs.pop('lgr_id', '')
        super(LGRCompareSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        for lgr_f in ['lgr_1', 'lgr_2']:
            self.fields[lgr_f].choices = ((name, name) for name in session_lgrs)
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


class LGRAnnotateSelector(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use for annotation'),
                            required=True)

    labels = forms.FileField(label=_("Labels"),
                             help_text=_('List of labels to use in diff. '
                                         'File must be encoded in UNIX format.'),
                             required=True)

    email = forms.EmailField(label=_("E-mail"),
                             help_text=_('Provide your e-mail address'),
                             required=True)

    def __init__(self, *args, **kwargs):
        session_lgrs = kwargs.pop('session_lgrs', [])
        lgr_id = kwargs.pop('lgr_id', '')
        super(LGRAnnotateSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((name, name) for name in session_lgrs)
        self.fields['lgr'].initial = lgr_id


