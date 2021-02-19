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
from .api import _prepare_validation_html_file_response
from .views.codepoints.codepoint import (CodePointUpdateReferencesView,
                                         CodePointDeleteView,
                                         VariantUpdateReferencesView,
                                         VariantDeleteView, CodePointView)
from .views.codepoints.importer import AddRangeView, AddCodepointFromScriptView, ImportCodepointsFromFileView
from .views.codepoints.list import (ExpandRangeView,
                                    ExpandRangesView,
                                    PopulateVariantsView,
                                    ListCodePointsJsonView,
                                    ListCodePointsView)
from .views.create import (DeleteLGRView,
                           ImportReferenceLGRView,
                           NewLGRView,
                           ImportLGRView)
from .views.export import LGRRenderXMLView
from .views.reference import ReferenceView, ListReferenceJsonView, AddReferenceAjaxView, DeleteReferenceView
from .views.set import EmbeddedLGRsView
from .views.tag import ListTagView, ListTagJsonView, DeleteTagView
from .views.validate import ValidateLGRView
from .views.metadata import MetadataView, LanguageAutocomplete
from .views.rule import ListRuleView, RuleEditClassAjaxView, RuleEditRuleAjaxView, RuleEditActionAjaxView

register_converter(FileNameConverter, 'filename')
register_converter(LgrSlugConverter, 'lgr')
register_converter(CodePointSlugConverter, 'cp')
register_converter(VarSlugConverter, 'var')
register_converter(TagSlugConverter, 'tag')
register_converter(ReferenceIdConverter, 'ref')
register_converter(ActionIndexConverter, 'action')

urlpatterns = [
    # Import/Creation functions
    path('import/ref/<filename:filename>/', ImportReferenceLGRView.as_view(), name='import_reference_lgr'),
    path('lgr/<lgr:lgr_id>/d/', DeleteLGRView.as_view(), name='delete_lgr'),
    path('new/', NewLGRView.as_view(), name='new_lgr'),
    path('import/', ImportLGRView.as_view(), name='import_lgr'),

    # View/Export functions
    path('lgr/view/<lgr:lgr_id>.xml', LGRRenderXMLView.as_view(), name='view_lgr_xml'),
    path('lgr/view/<lgr:lgr_set_id>/<lgr:lgr_id>.xml', LGRRenderXMLView.as_view(), name='view_lgr_xml'),
    path('lgr/download/<lgr:lgr_id>.xml', LGRRenderXMLView.as_view(), kwargs={'force_download': True},
         name='download_lgr_xml'),
    path('lgr/download/<lgr:lgr_set_id>/<lgr:lgr_id>.xml', LGRRenderXMLView.as_view, kwargs={'force_download': True},
         name='download_lgr_xml'),

    # Reference management functions
    path('lgr/<lgr:lgr_id>/a/references/', AddReferenceAjaxView.as_view(), name='reference_add_ajax'),
    path('lgr/<lgr:lgr_id>/references/', ReferenceView.as_view(), name='references'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/references/', ReferenceView.as_view(), name='references'),
    path('lgr/<lgr:lgr_id>/references.json/', ListReferenceJsonView.as_view(), name='references_json'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/references.json/', ListReferenceJsonView.as_view(), name='references_json'),
    path('lgr/<lgr:lgr_id>/d/references/<ref:ref_id>', DeleteReferenceView.as_view(), name='reference_delete'),

    # Metadata management functions,
    path('lgr/<lgr:lgr_id>/metadata/', MetadataView.as_view(), name='metadata'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/metadata/', MetadataView.as_view(), name='metadata'),

    # Tags management functions
    path('lgr/<lgr:lgr_id>/tags', ListTagView.as_view(), name='tags'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/tags', ListTagView.as_view(), name='tags'),
    path('lgr/<lgr:lgr_id>/d/tags/<tag:tag_id>', DeleteTagView, name='tag_delete'),
    path('lgr/<lgr:lgr_id>/tags/<tag:tag_id>', ListTagJsonView.as_view(), name='tag_list_json'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/tags/<tag:tag_id>', ListTagJsonView.as_view(), name='tag_list_json'),

    # Rules functions
    path('lgr/<lgr:lgr_id>/rules/', ListRuleView.as_view(), name='rules'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/rules/', ListRuleView.as_view(), name='rules'),

    path('lgr/<lgr:lgr_id>/rules/class/edit/<str:clsname>/', RuleEditClassAjaxView.as_view(), name='rule_edit_class'),
    path('lgr/<lgr:lgr_id>/rules/rule/edit/<str:rulename>/', RuleEditRuleAjaxView.as_view(), name='rule_edit_rule'),
    path('lgr/<lgr:lgr_id>/rules/action/edit/(<action:action_idx>/', RuleEditActionAjaxView.as_view(),
         name='rule_edit_action'),

    # Embedded LGR function
    path('lgr/<lgr:lgr_id>/embedded/', EmbeddedLGRsView.as_view(), name='embedded_lgrs'),

    # Validation function
    path('lgr/<lgr:lgr_id>/validate_lgr/', ValidateLGRView.as_view(), name='validate_lgr'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/validate_lgr/', ValidateLGRView.as_view(), name='validate_lgr'),
    path('lgr/<lgr:lgr_id>/validate_lgr/s/', ValidateLGRView.as_view(),
         kwargs={'output_func': _prepare_validation_html_file_response}, name='validate_lgr_save'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/validate_lgr/s/', ValidateLGRView.as_view(),
         kwargs={'output_func': _prepare_validation_html_file_response}, name='validate_lgr_save'),

    # Codepoint functions
    path('lgr/<lgr:lgr_id>/v/<cp:codepoint_id>/', CodePointView.as_view(), name='codepoint_view'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/v/<cp:codepoint_id>/', CodePointView.as_view(), name='codepoint_view'),
    path('lgr/<lgr:lgr_id>/e/<cp:codepoint_id>/', ExpandRangeView.as_view(), name='expand_range'),
    path('lgr/<lgr:lgr_id>/e/', ExpandRangesView.as_view(), name='expand_ranges'),
    path('lgr/<lgr:lgr_id>/p/', PopulateVariantsView.as_view(), name='populate_variants'),
    path('lgr/<lgr:lgr_id>/r/<cp:codepoint_id>/', CodePointUpdateReferencesView.as_view(),
         name='codepoint_update_refs'),
    path('lgr/<lgr:lgr_id>/vr/<cp:codepoint_id>/<var:var_slug>/', VariantUpdateReferencesView.as_view(),
         name='var_update_refs'),
    path('lgr/<lgr:lgr_id>/d/<cp:codepoint_id>/', CodePointDeleteView.as_view(), name='codepoint_delete'),
    path('lgr/<lgr:lgr_id>/d/<cp:codepoint_id>/<var:var_slug>', VariantDeleteView.as_view(), name='variant_delete'),
    path('lgr/<lgr:lgr_id>/r/', AddRangeView.as_view(), name='add_range'),
    path('lgr/<lgr:lgr_id>/rs/', AddCodepointFromScriptView.as_view(), name='add_from_script'),
    path('lgr/<lgr:lgr_id>/i/', ImportCodepointsFromFileView.as_view(), name='import_from_file'),
    path('lgr/<lgr:lgr_id>/', ListCodePointsView.as_view(), name='codepoint_list'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/', ListCodePointsView.as_view(), name='codepoint_list'),
    path('lgr/<lgr:lgr_id>/json', ListCodePointsJsonView.as_view(), name='codepoint_list_json'),
    path('lgr/<lgr:lgr_set_id>/<lgr:lgr_id>/json', ListCodePointsJsonView.as_view(), name='codepoint_list_json'),

    # autocompletion
    path('language-autocomplete/', LanguageAutocomplete.as_view(), name='language-autocomplete'),
]
