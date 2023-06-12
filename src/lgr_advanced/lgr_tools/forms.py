# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from lgr_advanced.widgets import DataSelectWidget
from lgr_advanced.lgr_editor.forms import FILE_FIELD_ENCODING_HELP
from lgr_advanced.models import LgrModel
from lgr_models.models.lgr import RzLgr

LGR_COMPARE_ACTIONS = (
    ("UNION", _("Union")),
    ("INTERSECTION", _("Intersection")),
    ("DIFF", _("Diff")))


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
        user = kwargs.pop('user', [])
        super(LGRCompareSelector, self).__init__(*args, **kwargs)
        need_empty = False
        lgr_sets = LgrModel.objects.filter(owner=user, set_info__isnull=False)
        lgrs = LgrModel.objects.filter(owner=user, set_info__isnull=True)
        all_lgrs = LgrModel.objects.filter(owner=user)
        if lgr_sets.count() < 2 or lgrs.count() < 2:
            need_empty = True

        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr_1'].choices = ((_('LGR'), [(lgr_obj.pk, lgr_obj.name) for lgr_obj in lgrs]),
                                        (_('LGR set'), [(lgr_obj.pk, lgr_obj.name) for lgr_obj in lgr_sets]))
        self.fields['lgr_2'].choices = ((lgr_obj.pk, lgr_obj.name) for lgr_obj in all_lgrs)
        self.fields['lgr_1'].widget.data = {lgr_obj.pk: {'is-set': 'yes' if lgr_obj.is_set() else 'no'}
                                            for lgr_obj in all_lgrs}
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
                             help_text=f"{_('List of labels to use in tool.')} {FILE_FIELD_ENCODING_HELP}",
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
        user = kwargs.pop('user', [])
        super(LGRDiffSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        for lgr in ['lgr_1', 'lgr_2']:
            self.fields[lgr].choices = ((lgr_obj.pk, lgr_obj.name) for lgr_obj in
                                        LgrModel.objects.filter(owner=user,
                                                                set_info__isnull=True))


class LGRCollisionSelector(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use in tool'),
                            required=True)

    download_tlds = forms.BooleanField(label=_("Also check for collision with existing TLDs"),
                                       required=False)

    labels = forms.FileField(label=_("Labels"),
                             help_text=f"{_('List of labels to use in tool.')} {FILE_FIELD_ENCODING_HELP}")

    full_dump = forms.BooleanField(label=_("Full dump"),
                                   help_text=_('Print a full dump'),
                                   required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', [])
        super(LGRCollisionSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((lgr_obj.pk, lgr_obj.name) for lgr_obj in
                                      LgrModel.objects.filter(owner=user,
                                                              set_info__isnull=True))


class LGRSetCompatibleForm(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use in tool'),
                            required=True,
                            widget=DataSelectWidget)

    script = forms.ChoiceField(label=_("Script"),
                               help_text=_('The script used to validate the label'),
                               required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', [])
        super(LGRSetCompatibleForm, self).__init__(*args, **kwargs)
        lgr_sets = LgrModel.objects.filter(owner=user, set_info__isnull=False)
        lgrs = LgrModel.objects.filter(owner=user, set_info__isnull=True)

        lgr_scripts = set()
        for lgr in lgr_sets:
            scripts = []
            for lgr_in_set_obj in lgr.embedded_lgrs():
                lgr_in_set = lgr_in_set_obj.to_lgr()
                try:
                    scripts.append((lgr_in_set_obj.pk, lgr_in_set.metadata.languages[0]))
                except (AttributeError, IndexError):
                    pass
            lgr_scripts |= set(scripts)

        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((_('LGR'), [(lgr_obj.pk, lgr_obj.name) for lgr_obj in lgrs]),
                                      (_('LGR set'), [(lgr_obj.pk, lgr_obj.name) for lgr_obj in lgr_sets]))
        self.fields['lgr'].widget.data = {
            lgr_obj.pk: {'lgr-set': ','.join(str(pk) for pk in lgr_obj.embedded_lgrs().values_list('pk', flat=True))}
            for lgr_obj in lgr_sets
        }

        if lgr_scripts:
            self.fields['script'].choices = lgr_scripts


class LGRAnnotateSelector(LGRSetCompatibleForm):
    set_labels = forms.FileField(label=_("Allocated Set labels"),
                                 required=False,
                                 help_text="%s %s" % (
                                     _('Optional list of labels already allocated in the LGR set, that will be used to '
                                       'check for collisions when evaluating labels using the merged LGR set.'),
                                     FILE_FIELD_ENCODING_HELP))

    labels = forms.FileField(label=_("Labels"),
                             help_text=f"{_('List of labels to use in tool.')} {FILE_FIELD_ENCODING_HELP}",
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
        user = kwargs.pop('user', [])
        super(LGRHarmonizeSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs
        for field_name in ('lgr_1', 'lgr_2'):
            self.fields[field_name].choices = ((lgr_obj.pk, lgr_obj.name)
                                               for lgr_obj in LgrModel.objects.filter(owner=user,
                                                                                      set_info__isnull=True))
        self.fields['rz_lgr'].choices = [('', ''), ] + list((lgr_obj.pk, lgr_obj.name)
                                                            for lgr_obj in RzLgr.objects.filter(active=True))


class LGRComputeVariantsSelector(forms.Form):
    lgr = forms.ChoiceField(label=_("LGR"),
                            help_text=_('LGR to use in tool'),
                            required=True)

    labels = forms.FileField(label=_("Labels"),
                             help_text=f"{_('List of labels to use in tool.')} {FILE_FIELD_ENCODING_HELP}")

    include_mixed_script_variants = forms.BooleanField(label='',
                                                       widget=forms.CheckboxInput(),
                                                       required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', [])
        super(LGRComputeVariantsSelector, self).__init__(*args, **kwargs)
        # dynamically append the session LGRs (by copy, not by reference)
        self.fields['lgr'].choices = ((lgr_obj.pk, lgr_obj.name)
                                      for lgr_obj in LgrModel.objects.filter(owner=user,
                                                                             set_info__isnull=True))
