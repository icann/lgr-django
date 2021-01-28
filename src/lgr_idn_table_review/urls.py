# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from lgr_idn_table_review.views import IdnTableReviewModeView, IdnTableReviewSelectReferenceView
from lgr_web.converters import LgrSlugConverter

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('', IdnTableReviewModeView.as_view(), name='lgr_review_mode'),
    path('ref', IdnTableReviewSelectReferenceView.as_view(), name='lgr_review_select_reference'),
]
