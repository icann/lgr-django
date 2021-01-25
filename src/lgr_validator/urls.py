# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import register_converter, path

from lgr_web.converters import LgrSlugConverter
from . import views

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('eval/<lgr:lgr_id>/json/', views.validate_label_json, name='lgr_validate_json'),
    path('eval/<lgr:lgr_set_id>/<lgr:lgr_id>/json/', views.validate_label_json, name='lgr_validate_json'),
    path('eval/<lgr:lgr_id>/csv/', views.validate_label_csv, name='lgr_validate_csv'),
    path('eval/<lgr:lgr_set_id>/<lgr:lgr_id>/csv/', views.validate_label_csv, name='lgr_validate_csv'),
    path('eval/<lgr:lgr_id>/validate/', views.validate_label, name='lgr_validate_label'),
    path('eval/<lgr:lgr_set_id>/<lgr:lgr_id>/validate/', views.validate_label, name='lgr_validate_label'),
    path('eval/<lgr:lgr_id>/validate-nf/', views.validate_label_noframe,
         name='lgr_validate_label_noframe'),
    path('eval/<lgr:lgr_set_id>/<lgr:lgr_id>/validate-nf/', views.validate_label_noframe,
         name='lgr_validate_label_noframe'),
]
