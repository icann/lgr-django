# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url, patterns
from . import views

LGR_SLUG_FORMAT_WITH_OPT_SET = r'(?:(?P<lgr_set_id>[\w\_\-\.]+)/)?(?P<lgr_id>[\w\_\-\.]+)'
LGR_SLUG_FORMAT = r'(?P<lgr_id>[\w\_\-\.]+)'
CP_SLUG_FORMAT = r'(?P<codepoint_id>[0-9a-z-A-Z]{1,6}(-[0-9a-z-A-Z]{1,6})*)'
VAR_SLUG_FORMAT = r'(?P<var_slug>[0-9a-z-A-Z]{1,6}(-[0-9a-z-A-Z]{1,6})*,.*,.*)'

urlpatterns = patterns(
    '',

    # Import/Creation functions
    url(r'^import/ref/(?P<filename>[\w\_\-\.]+)/$',
        views.import_reference_lgr,
        name='import_reference_lgr'),
    url(r'^lgr/{}/d/$'.format(LGR_SLUG_FORMAT),
        views.delete_lgr,
        name='delete_lgr'),
    url(r'^new/$',
        views.new_lgr,
        name='new_lgr'),
    url(r'^import/$',
        views.import_lgr,
        name='import_lgr'),

    # Storage related functions
    url(r'^storage/(?P<filename>[\w\_\-\.]+)/dl/$',
        views.download_file,
        name='download_file'),
    url(r'^storage/(?P<filename>[\w\_\-\.]+)/rm/$',
        views.delete_file,
        name='delete_file'),

    # View/Export functions
    url(r'^lgr/view/{}.xml'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.view_lgr_xml,
        name='view_lgr_xml'),
    url(r'^lgr/download/{}.xml'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.view_lgr_xml, kwargs={'force_download': True},
        name='download_lgr_xml'),

    # Reference management functions
    url(r'^lgr/{}/references/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.reference_list,
        name='references'),
    url(r'^lgr/{}/references.json/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.reference_list_json,
        name='references_json'),
    url(r'^lgr/{}/a/references/$'.format(LGR_SLUG_FORMAT),
        views.add_reference_ajax,
        name='reference_add_ajax'),
    url(r'^lgr/{}/d/references/(?P<ref_id>[\w\_\-\.\s]+)$'.format(LGR_SLUG_FORMAT),
        views.delete_reference,
        name='reference_delete'),

    # Metadata management functions,
    url(r'^lgr/{}/metadata/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.MetadataView.as_view(),
        name='metadata'),

    # Rules functions
    url(r'^lgr/{}/rules/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.rule_list,
        name='rules'),

    url(r'^lgr/{}/rules/class/edit/(?P<clsname>.+)/$'.format(LGR_SLUG_FORMAT),
        views.rule_edit_class_ajax,
        name='rule_edit_class'),
    url(r'^lgr/{}/rules/rule/edit/(?P<rulename>.+)/$'.format(LGR_SLUG_FORMAT),
        views.rule_edit_rule_ajax,
        name='rule_edit_rule'),
    url(r'^lgr/{}/rules/action/edit/(?P<action_idx>-?\d+)/$'.format(LGR_SLUG_FORMAT),
        views.rule_edit_action_ajax,
        name='rule_edit_action'),

    # Embedded LGR function
    url(r'^lgr/{}/embedded/$'.format(LGR_SLUG_FORMAT),
        views.embedded_lgrs,
        name='embedded_lgrs'),

    # Summary function
    url(r'^lgr/{}/summary/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.validate_lgr,
        name='summary'),
    url(r'^lgr/{}/summary/s/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.save_summary,
        name='summary_save'),

    # Validation function
    url(r'^lgr/{}/validate/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.validate_label,
        name='lgr_validate_label'),
    url(r'^lgr/{}/validate-nf/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.validate_label_noframe,
        name='lgr_validate_label_noframe'),

    # Codepoint functions
    url(r'^lgr/default/$',
        views.codepoint_list,
        name='codepoint_list_default'),
    url(r'^lgr/{}/v/{}/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET, CP_SLUG_FORMAT),
        views.codepoint_view,
        name='codepoint_view'),
    url(r'^lgr/{}/e/{}/$'.format(LGR_SLUG_FORMAT, CP_SLUG_FORMAT),
        views.expand_range,
        name='expand_range'),
    url(r'^lgr/{}/e/$'.format(LGR_SLUG_FORMAT),
        views.expand_ranges,
        name='expand_ranges'),
    url(r'^lgr/{}/p/$'.format(LGR_SLUG_FORMAT),
        views.populate_variants,
        name='populate_variants'),
    url(r'^lgr/{}/r/{}/$'.format(LGR_SLUG_FORMAT, CP_SLUG_FORMAT),
        views.codepoint_update_refs,
        name='codepoint_update_refs'),
    url(r'^lgr/{}/vr/{}/{}/$'.format(LGR_SLUG_FORMAT, CP_SLUG_FORMAT, VAR_SLUG_FORMAT),
        views.var_update_refs,
        name='var_update_refs'),
    url(r'^lgr/{}/d/{}/$'.format(LGR_SLUG_FORMAT, CP_SLUG_FORMAT),
        views.codepoint_delete,
        name='codepoint_delete'),
    url(r'^lgr/{}/d/{}/{}$'.format(LGR_SLUG_FORMAT, CP_SLUG_FORMAT, VAR_SLUG_FORMAT),
        views.variant_delete,
        name='variant_delete'),
    url(r'^lgr/{}/r/$'.format(LGR_SLUG_FORMAT),
        views.AddRangeView.as_view(),
        name='add_range'),
    url(r'^lgr/{}/rs/$'.format(LGR_SLUG_FORMAT),
        views.AddCodepointFromScriptView.as_view(),
        name='add_from_script'),
    url(r'^lgr/{}/i/$'.format(LGR_SLUG_FORMAT),
        views.ImportCodepointsFromFileView.as_view(),
        name='import_from_file'),
    url(r'^lgr/{}/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.codepoint_list,
        name='codepoint_list'),

    url(r'^label_forms/$',
        views.label_forms,
        name='lgr_label_forms'),

    url(r'^about/$',
        views.about,
        name='about'),
)
