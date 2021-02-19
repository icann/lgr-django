# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import register_converter, path

from lgr_web.converters import LgrSlugConverter
from .views import ValidateLabelView, ValidateLabelNoFrameView, ValidateLabelJsonView, ValidateLabelCSVView

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('eval/<lgr:lgr_id>/json/', ValidateLabelJsonView.as_view(), name='lgr_validate_json'),
    path('eval/<lgr:lgr_set_id>/<lgr:lgr_id>/json/', ValidateLabelJsonView.as_view(), name='lgr_validate_json'),
    path('eval/<lgr:lgr_id>/csv/', ValidateLabelCSVView.as_view(), name='lgr_validate_csv'),
    path('eval/<lgr:lgr_set_id>/<lgr:lgr_id>/csv/', ValidateLabelCSVView.as_view(), name='lgr_validate_csv'),
    path('eval/<lgr:lgr_id>/validate/', ValidateLabelView.as_view(), name='lgr_validate_label'),
    path('eval/<lgr:lgr_set_id>/<lgr:lgr_id>/validate/', ValidateLabelView.as_view(), name='lgr_validate_label'),
    path('eval/<lgr:lgr_id>/validate-nf/', ValidateLabelNoFrameView.as_view(),
         name='lgr_validate_label_noframe'),
    path('eval/<lgr:lgr_set_id>/<lgr:lgr_id>/validate-nf/', ValidateLabelNoFrameView.as_view(),
         name='lgr_validate_label_noframe'),
]
