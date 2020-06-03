# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from . import views
from .views import LanguageAutocomplete

LGR_SLUG_FORMAT_WITH_OPT_SET = r'(?:(?P<lgr_set_id>[\w\_\-\.]+)/)?(?P<lgr_id>[\w\_\-\.]+)'
LGR_SLUG_FORMAT = r'(?P<lgr_id>[\w\_\-\.]+)'
CP_SLUG_FORMAT = r'(?P<codepoint_id>[0-9a-z-A-Z]{1,6}(-[0-9a-z-A-Z]{1,6})*)'
VAR_SLUG_FORMAT = r'(?P<var_slug>[0-9a-z-A-Z]{1,6}(-[0-9a-z-A-Z]{1,6})*,.*,.*)'
TAG_SLUG_FORMAT = r'(?P<tag_id>[0-9a-zA-Z._:\-]+)'

urlpatterns = [
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
    url(r'^lgr/{}/a/references/$'.format(LGR_SLUG_FORMAT),
        views.add_reference_ajax,
        name='reference_add_ajax'),
    url(r'^lgr/{}/references/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.reference_list,
        name='references'),
    url(r'^lgr/{}/references.json/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.reference_list_json,
        name='references_json'),
    url(r'^lgr/{}/d/references/(?P<ref_id>[\w\_\-\.\s\:]+)$'.format(LGR_SLUG_FORMAT),
        views.delete_reference,
        name='reference_delete'),

    # Metadata management functions,
    url(r'^lgr/{}/metadata/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.MetadataView.as_view(),
        name='metadata'),

    # Tags management functions
    url(r'^lgr/{}/tags$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.tag_list,
        name='tags'),
    url(r'^lgr/{}/d/tags/{}$'.format(LGR_SLUG_FORMAT, TAG_SLUG_FORMAT),
        views.delete_tag,
        name='tag_delete'),
    url(r'^lgr/{}/tags/{}$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET, TAG_SLUG_FORMAT),
        views.tag_list_json,
        name='tag_list_json'),

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

    # Validation function
    url(r'^lgr/{}/validate_lgr/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.validate_lgr,
        name='validate_lgr'),
    url(r'^lgr/{}/validate_lgr/s/$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.validate_lgr_save,
        name='validate_lgr_save'),

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
    url(r'lgr/{}/json$'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.codepoint_list_json,
        name='codepoint_list_json'),

    url(r'^label_forms/$',
        views.label_forms,
        name='lgr_label_forms'),

    # autocompletion
    url(r'^language-autocomplete/$',
        LanguageAutocomplete.as_view(),
        name='language-autocomplete'),

    url(r'^about/$',
        views.about,
        name='about'),
]
