# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from lgr_web.converters import LgrSlugConverter
from .views import (LGRCompareView,
                    LGRDiffView,
                    LGRCollisionView,
                    LGRAnnotateView,
                    LGRCrossScriptVariantsView,
                    LGRHarmonizeView,
                    LGRComputeVariants)

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('comp/', LGRCompareView.as_view(), name='lgr_tools_compare'),
    path('comp/<lgr:lgr_id>', LGRCompareView.as_view(), name='lgr_tools_compare'),
    path('diff/', LGRDiffView.as_view(), name='lgr_tools_diff'),
    path('diff/<lgr:lgr_id>', LGRDiffView.as_view(), name='lgr_tools_diff'),
    path('coll/', LGRCollisionView.as_view(), name='lgr_tools_collisions'),
    path('coll/<lgr:lgr_id>', LGRCollisionView.as_view(), name='lgr_tools_collisions'),
    path('annotate/', LGRAnnotateView.as_view(), name='lgr_tools_annotate'),
    path('annotate/<lgr:lgr_id>', LGRAnnotateView.as_view(), name='lgr_tools_annotate'),
    path('variants/', LGRComputeVariants.as_view(), name='lgr_tools_variants'),
    path('variants/<lgr:lgr_id>', LGRComputeVariants.as_view(), name='lgr_tools_variants'),
    path('cross-script/', LGRCrossScriptVariantsView.as_view(), name='lgr_tools_cross_script'),
    path('cross-script/<lgr:lgr_id>', LGRCrossScriptVariantsView.as_view(), name='lgr_tools_cross_script'),
    path('harmonization/', LGRHarmonizeView.as_view(), name='lgr_tools_harmonize'),
    path('harmonization/<lgr:lgr_id>', LGRHarmonizeView.as_view(), name='lgr_tools_harmonize'),
]
