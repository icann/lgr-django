# -*- coding: utf-8 -*-
from django.urls import path

from .views import (LGRCompareView,
                    LGRDiffView,
                    LGRCollisionView,
                    LGRAnnotateView,
                    LGRHarmonizeView,
                    LGRComputeVariants)

urlpatterns = [
    path('comp/', LGRCompareView.as_view(), name='lgr_tools_compare'),
    path('comp/<int:lgr_pk>', LGRCompareView.as_view(), name='lgr_tools_compare'),
    path('diff/', LGRDiffView.as_view(), name='lgr_tools_diff'),
    path('diff/<int:lgr_pk>', LGRDiffView.as_view(), name='lgr_tools_diff'),
    path('coll/', LGRCollisionView.as_view(), name='lgr_tools_collisions'),
    path('coll/<int:lgr_pk>', LGRCollisionView.as_view(), name='lgr_tools_collisions'),
    path('annotate/', LGRAnnotateView.as_view(), name='lgr_tools_annotate'),
    path('annotate/<int:lgr_pk>', LGRAnnotateView.as_view(), name='lgr_tools_annotate'),
    path('variants/', LGRComputeVariants.as_view(), name='lgr_tools_variants'),
    path('variants/<int:lgr_pk>', LGRComputeVariants.as_view(), name='lgr_tools_variants'),
    path('harmonization/', LGRHarmonizeView.as_view(), name='lgr_tools_harmonize'),
    path('harmonization/<int:lgr_pk>', LGRHarmonizeView.as_view(), name='lgr_tools_harmonize'),
]
