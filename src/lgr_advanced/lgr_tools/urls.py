# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from lgr_web.converters import LgrSlugConverter
from . import views

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('comp/<lgr:lgr_id>', views.lgr_compare, name='lgr_tools_compare'),
    path('diff/<lgr:lgr_id>', views.lgr_diff, name='lgr_tools_diff'),
    path('coll/<lgr:lgr_id>', views.lgr_collisions, name='lgr_tools_collisions'),
    path('annotate/<lgr:lgr_id>', views.lgr_annotate, name='lgr_tools_annotate'),
    path('variants/<lgr:lgr_id>', views.lgr_compute_variants, name='lgr_tools_variants'),
    path('cross-script/<lgr:lgr_id>', views.lgr_cross_script_variants, name='lgr_tools_cross_script'),
    path('harmonization/<lgr:lgr_id>', views.lgr_harmonize, name='lgr_tools_harmonize'),
]
