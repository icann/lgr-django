# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from lgr_web.converters import (LgrSlugConverter,
                                CodePointSlugConverter,
                                VarSlugConverter,
                                TagSlugConverter,
                                FileNameConverter,
                                ReferenceIdConverter,
                                ActionIndexConverter)
from . import views
from .views import LanguageAutocomplete

register_converter(FileNameConverter, 'filename')
register_converter(LgrSlugConverter, 'lgr')
register_converter(CodePointSlugConverter, 'cp')
register_converter(VarSlugConverter, 'var')
register_converter(TagSlugConverter, 'tag')
register_converter(ReferenceIdConverter, 'ref')
register_converter(ActionIndexConverter, 'action')

urlpatterns = [
    # Import/Creation functions
    path('import/ref/<filename:filename>/', views.import_reference_lgr, name='import_reference_lgr'),
    path('lgr/<lgr:lgr_id>/d/', views.delete_lgr, name='delete_lgr'),
    path('new/', views.new_lgr, name='new_lgr'),
    path('import/', views.import_lgr, name='import_lgr'),

    # View/Export functions
    path('lgr/view/<lgr:lgr_id>.xml', views.view_lgr_xml, name='view_lgr_xml'),
    path('lgr/view/<lgr:lgr_set_id>/<lgr:lgr_id>.xml', views.view_lgr_xml, name='view_lgr_xml'),
    path('lgr/download/<lgr:lgr_id>.xml', views.view_lgr_xml, kwargs={'force_download': True},
         name='download_lgr_xml'),
    path('lgr/download/<lgr:lgr_set_id>/<lgr:lgr_id>.xml', views.view_lgr_xml, kwargs={'force_download': True},
         name='download_lgr_xml'),

    # Reference management functions
    path('lgr/<lgr:lgr_id>/a/references/', views.add_reference_ajax, name='reference_add_ajax'),
    path('lgr/<lgr:lgr_id>/references/', views.reference_list, name='references'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/references/', views.reference_list, name='references'),
    path('lgr/<lgr:lgr_id>/references.json/', views.reference_list_json, name='references_json'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/references.json/', views.reference_list_json, name='references_json'),
    path('lgr/<lgr:lgr_id>/d/references/<ref:ref_id>', views.delete_reference, name='reference_delete'),

    # Metadata management functions,
    path('lgr/<lgr:lgr_id>/metadata/', views.MetadataView.as_view(), name='metadata'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/metadata/', views.MetadataView.as_view(), name='metadata'),

    # Tags management functions
    path('lgr/<lgr:lgr_id>/tags', views.tag_list, name='tags'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/tags', views.tag_list, name='tags'),
    path('lgr/<lgr:lgr_id>/d/tags/<tag:tag_id>', views.delete_tag, name='tag_delete'),
    path('lgr/<lgr:lgr_id>/tags/<tag:tag_id>', views.tag_list_json, name='tag_list_json'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/tags/<tag:tag_id>', views.tag_list_json, name='tag_list_json'),

    # Rules functions
    path('lgr/<lgr:lgr_id>/rules/', views.rule_list, name='rules'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/rules/', views.rule_list, name='rules'),

    path('lgr/<lgr:lgr_id>/rules/class/edit/<str:clsname>/', views.rule_edit_class_ajax, name='rule_edit_class'),
    path('lgr/<lgr:lgr_id>/rules/rule/edit/<str:rulename>/', views.rule_edit_rule_ajax, name='rule_edit_rule'),
    path('lgr/<lgr:lgr_id>/rules/action/edit/(<action:action_idx>/', views.rule_edit_action_ajax,
         name='rule_edit_action'),

    # Embedded LGR function
    path('lgr/<lgr:lgr_id>/embedded/', views.embedded_lgrs, name='embedded_lgrs'),

    # Validation function
    path('lgr/<lgr:lgr_id>/validate_lgr/', views.validate_lgr, name='validate_lgr'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/validate_lgr/', views.validate_lgr, name='validate_lgr'),
    path('lgr/<lgr:lgr_id>/validate_lgr/s/', views.validate_lgr_save, name='validate_lgr_save'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/validate_lgr/s/', views.validate_lgr_save, name='validate_lgr_save'),

    # Codepoint functions
    path('lgr/default/', views.codepoint_list, name='codepoint_list_default'),
    path('lgr/<lgr:lgr_id>/v/<cp:codepoint_id>/', views.codepoint_view, name='codepoint_view'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/v/<cp:codepoint_id>/', views.codepoint_view, name='codepoint_view'),
    path('lgr/<lgr:lgr_id>/e/<cp:codepoint_id>/', views.expand_range, name='expand_range'),
    path('lgr/<lgr:lgr_id>/e/', views.expand_ranges, name='expand_ranges'),
    path('lgr/<lgr:lgr_id>/p/', views.populate_variants, name='populate_variants'),
    path('lgr/<lgr:lgr_id>/r/<cp:codepoint_id>/', views.codepoint_update_refs, name='codepoint_update_refs'),
    path('lgr/<lgr:lgr_id>/vr/<cp:codepoint_id>/<var:var_slug>/', views.var_update_refs, name='var_update_refs'),
    path('lgr/<lgr:lgr_id>/d/<cp:codepoint_id>/', views.codepoint_delete, name='codepoint_delete'),
    path('lgr/<lgr:lgr_id>/d/<cp:codepoint_id>/<var:var_slug>', views.variant_delete, name='variant_delete'),
    path('lgr/<lgr:lgr_id>/r/', views.AddRangeView.as_view(), name='add_range'),
    path('lgr/<lgr:lgr_id>/rs/', views.AddCodepointFromScriptView.as_view(), name='add_from_script'),
    path('lgr/<lgr:lgr_id>/i/', views.ImportCodepointsFromFileView.as_view(), name='import_from_file'),
    path('lgr/<lgr:lgr_id>/', views.codepoint_list, name='codepoint_list'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/', views.codepoint_list, name='codepoint_list'),
    path('lgr/<lgr:lgr_id>/json', views.codepoint_list_json, name='codepoint_list_json'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/json', views.codepoint_list_json, name='codepoint_list_json'),

    # autocompletion
    path('language-autocomplete/', LanguageAutocomplete.as_view(), name='language-autocomplete'),
]
