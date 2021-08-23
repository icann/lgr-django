# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path

from .views import ValidateLabelView, ValidateLabelNoFrameView, ValidateLabelJsonView, ValidateLabelCSVView

urlpatterns = [
    path('eval/<int:lgr_pk>/json/', ValidateLabelJsonView.as_view(), name='lgr_validate_json'),
    path('set/eval/<int:lgr_pk>/json/', ValidateLabelJsonView.as_view(), name='lgr_validate_json_set',
         kwargs={'in_set': True}),
    path('eval/<int:lgr_pk>/csv/', ValidateLabelCSVView.as_view(), name='lgr_validate_csv'),
    path('set/eval/<int:lgr_pk>/csv/', ValidateLabelCSVView.as_view(), name='lgr_validate_csv_set',
         kwargs={'in_set': True}),
    path('eval/<int:lgr_pk>/validate/', ValidateLabelView.as_view(), name='lgr_validate_label'),
    path('set/eval/<int:lgr_pk>/validate/', ValidateLabelView.as_view(), name='lgr_validate_label_set',
         kwargs={'in_set': True}),
    path('eval/<int:lgr_pk>/validate-nf/', ValidateLabelNoFrameView.as_view(),
         name='lgr_validate_label_noframe'),
    path('set/eval/<int:lgr_pk>/validate-nf/', ValidateLabelNoFrameView.as_view(),
         name='lgr_validate_label_noframe_set', kwargs={'in_set': True}),
]
