# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from lgr_utils.converters import LgrModelConverter
from .views import ValidateLabelView, ValidateLabelNoFrameView, ValidateLabelJsonView, ValidateLabelCSVView

register_converter(LgrModelConverter, 'lgr_model')

urlpatterns = [
    path('eval/<lgr_model:model>/<int:lgr_pk>/json/', ValidateLabelJsonView.as_view(), name='lgr_validate_json'),
    path('eval/<lgr_model:model>/<int:lgr_pk>/csv/', ValidateLabelCSVView.as_view(), name='lgr_validate_csv'),
    path('eval/<lgr_model:model>/<int:lgr_pk>/validate/', ValidateLabelView.as_view(), name='lgr_validate_label'),
    path('eval/<lgr_model:model>/<int:lgr_pk>/validate-nf/', ValidateLabelNoFrameView.as_view(),
         name='lgr_validate_label_noframe'),
]
