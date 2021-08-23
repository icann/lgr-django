# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path

from lgr_idn_table_review.idn_tool.views import (IdnTableReviewModeView,
                                                 IdnTableReviewSelectReferenceView,
                                                 IdnTableReviewListReports,
                                                 IdnTableReviewListReport,
                                                 IdnTableReviewDisplayIdnTable, RefLgrAutocomplete)

urlpatterns = [
    path('', IdnTableReviewModeView.as_view(), name='lgr_review_mode'),
    path('ref/<str:report_id>', IdnTableReviewSelectReferenceView.as_view(), name='lgr_review_select_reference'),
    path('reports', IdnTableReviewListReports.as_view(), name='lgr_review_reports'),
    path('report/<str:report_id>', IdnTableReviewListReport.as_view(), name='lgr_review_report'),
    path('view/<int:lgr_pk>', IdnTableReviewDisplayIdnTable.as_view(), name='lgr_review_display_idn_table'),

    # autocompletion
    path('ref-lgr-autocomplete/', RefLgrAutocomplete.as_view(), name='ref-lgr-autocomplete'),
]
