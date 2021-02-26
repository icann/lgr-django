# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from lgr_idn_table_review.tool.views import (IdnTableReviewModeView,
                                             IdnTableReviewSelectReferenceView,
                                             IdnTableReviewListReportFolders,
                                             IdnTableReviewListReports,
                                             IdnTableReviewDisplayIdnTable, RefLgrAutocomplete)
from lgr_web.converters import LgrSlugConverter

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('', IdnTableReviewModeView.as_view(), name='lgr_review_mode'),
    path('ref/<str:report_id>', IdnTableReviewSelectReferenceView.as_view(), name='lgr_review_select_reference'),
    path('reports', IdnTableReviewListReportFolders.as_view(), name='lgr_review_report_folders'),
    path('report/<str:folder>', IdnTableReviewListReports.as_view(), name='lgr_review_reports'),
    path('view/<str:report_id>/<lgr:lgr_id>', IdnTableReviewDisplayIdnTable.as_view(),
         name='lgr_review_display_idn_table'),

    # autocompletion
    path('ref-lgr-autocomplete/', RefLgrAutocomplete.as_view(), name='ref-lgr-autocomplete'),
]
