# -*- coding: utf-8 -*-
from django.urls import path

from lgr_idn_table_review.idn_icann.views import IdnTableIcannModeView, IdnTableIcannListReports

urlpatterns = [
    path('', IdnTableIcannModeView.as_view(), name='lgr_idn_icann_mode'),
    path('report/<str:folder>', IdnTableIcannListReports.as_view(), name='lgr_idn_icann_reports'),
]
