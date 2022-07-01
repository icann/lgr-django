# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from lgr_utils.converters import LgrModelConverter
from lgr_web.converters import (CodePointSlugConverter,
                                VarSlugConverter,
                                TagSlugConverter,
                                FileNameConverter,
                                ReferenceIdConverter,
                                ActionIndexConverter)
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
                           ImportReferenceLGRFromFileView,
                           ImportReferenceLGRView,
                           NewLGRView,
                           ImportLGRView)
from .views.metadata import MetadataView
from .views.reference import ReferenceView, ListReferenceJsonView, AddReferenceAjaxView, DeleteReferenceView
from .views.rule import ListRuleView, RuleEditClassAjaxView, RuleEditRuleAjaxView, RuleEditActionAjaxView
from .views.set import EmbeddedLGRsView
from .views.tag import ListTagView, ListTagJsonView, DeleteTagView
from .views.validate import ValidateLGRView

register_converter(FileNameConverter, 'filename')
register_converter(CodePointSlugConverter, 'cp')
register_converter(VarSlugConverter, 'var')
register_converter(TagSlugConverter, 'tag')
register_converter(ReferenceIdConverter, 'ref')
register_converter(ActionIndexConverter, 'action')
register_converter(LgrModelConverter, 'lgr_model')

urlpatterns = [
    # Import/Creation functions
    path('import/ref/<filename:filename>/', ImportReferenceLGRFromFileView.as_view(),
         name='import_reference_lgr_from_file'),
    path('import/ref/<lgr_model:model>/<int:lgr_pk>', ImportReferenceLGRView.as_view(), name='import_reference_lgr'),
    path('lgr/<int:lgr_pk>/d/', DeleteLGRView.as_view(), name='delete_lgr'),
    path('new/', NewLGRView.as_view(), name='new_lgr'),
    path('import/', ImportLGRView.as_view(), name='import_lgr'),

    # Reference management functions
    path('lgr/<int:lgr_pk>/a/references/', AddReferenceAjaxView.as_view(), name='reference_add_ajax'),
    path('<lgr_model:model>/<int:lgr_pk>/references/', ReferenceView.as_view(), name='references'),
    path('<lgr_model:model>/<int:lgr_pk>/references.json/', ListReferenceJsonView.as_view(), name='references_json'),
    path('lgr/<int:lgr_pk>/d/references/<ref:ref_id>', DeleteReferenceView.as_view(), name='reference_delete'),

    # Metadata management functions,
    path('<lgr_model:model>/<int:lgr_pk>/metadata/', MetadataView.as_view(), name='metadata'),

    # Tags management functions
    path('<lgr_model:model>/<int:lgr_pk>/tags', ListTagView.as_view(), name='tags'),
    path('lgr/<int:lgr_pk>/d/tags/<tag:tag_id>', DeleteTagView.as_view(), name='tag_delete'),
    path('<lgr_model:model>/<int:lgr_pk>/tags/<tag:tag_id>', ListTagJsonView.as_view(), name='tag_list_json'),

    # Rules functions
    path('<lgr_model:model>/<int:lgr_pk>/rules/', ListRuleView.as_view(), name='rules'),

    path('lgr/<int:lgr_pk>/rules/class/edit/<str:clsname>/', RuleEditClassAjaxView.as_view(), name='rule_edit_class'),
    path('lgr/<int:lgr_pk>/rules/rule/edit/<str:rulename>/', RuleEditRuleAjaxView.as_view(), name='rule_edit_rule'),
    path('lgr/<int:lgr_pk>/rules/action/edit/(<action:action_idx>/', RuleEditActionAjaxView.as_view(),
         name='rule_edit_action'),

    # Embedded LGR function
    path('lgr/<int:lgr_pk>/embedded/', EmbeddedLGRsView.as_view(), name='embedded_lgrs'),

    # Validation function
    path('<lgr_model:model>/<int:lgr_pk>/validate_lgr/', ValidateLGRView.as_view(), name='validate_lgr'),
    path('<lgr_model:model>/<int:lgr_pk>/validate_lgr/s/', ValidateLGRView.as_view(), name='validate_lgr_save',
         kwargs={'output_func': _prepare_validation_html_file_response}),

    # Codepoint functions
    path('<lgr_model:model>/<int:lgr_pk>/v/<cp:codepoint_id>/', CodePointView.as_view(), name='codepoint_view'),
    path('lgr/<int:lgr_pk>/e/<cp:codepoint_id>/', ExpandRangeView.as_view(), name='expand_range'),
    path('lgr/<int:lgr_pk>/e/', ExpandRangesView.as_view(), name='expand_ranges'),
    path('lgr/<int:lgr_pk>/p/', PopulateVariantsView.as_view(), name='populate_variants'),
    path('lgr/<int:lgr_pk>/r/<cp:codepoint_id>/', CodePointUpdateReferencesView.as_view(),
         name='codepoint_update_refs'),
    path('lgr/<int:lgr_pk>/vr/<cp:codepoint_id>/<var:var_slug>/', VariantUpdateReferencesView.as_view(),
         name='var_update_refs'),
    path('lgr/<int:lgr_pk>/d/<cp:codepoint_id>/', CodePointDeleteView.as_view(), name='codepoint_delete'),
    path('lgr/<int:lgr_pk>/d/<cp:codepoint_id>/<var:var_slug>', VariantDeleteView.as_view(), name='variant_delete'),
    path('lgr/<int:lgr_pk>/r/', AddRangeView.as_view(), name='add_range'),
    path('lgr/<int:lgr_pk>/rs/', AddCodepointFromScriptView.as_view(), name='add_from_script'),
    path('lgr/<int:lgr_pk>/i/', ImportCodepointsFromFileView.as_view(), name='import_from_file'),
    path('<lgr_model:model>/<int:lgr_pk>/', ListCodePointsView.as_view(), name='codepoint_list'),
    path('<lgr_model:model>/<int:lgr_pk>/json', ListCodePointsJsonView.as_view(), name='codepoint_list_json'),
]
