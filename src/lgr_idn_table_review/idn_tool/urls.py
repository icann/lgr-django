# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from lgr_idn_table_review.idn_tool.views import (IdnTableReviewModeView,
                                                 IdnTableReviewSelectReferenceView,
                                                 IdnTableReviewListReports,
                                                 IdnTableReviewListReport,
                                                 IdnTableReviewDeleteReport)
from lgr_web.converters import FileNameConverter

register_converter(FileNameConverter, 'filename')

urlpatterns = [
    path('', IdnTableReviewModeView.as_view(), name='lgr_review_mode'),
    path('ref/<filename:report_id>', IdnTableReviewSelectReferenceView.as_view(), name='lgr_review_select_reference'),
    path('reports', IdnTableReviewListReports.as_view(), name='lgr_review_reports'),
    path('report/<filename:report_id>', IdnTableReviewListReport.as_view(), name='lgr_review_report'),
    path('report/<filename:report_id>/rm', IdnTableReviewDeleteReport.as_view(), name='lgr_review_delete_report'),
]
