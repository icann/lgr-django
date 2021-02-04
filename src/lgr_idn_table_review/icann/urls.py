# -*- coding: utf-8 -*-
from django.urls import path

from lgr_idn_table_review.icann.views import IdnTableIcannModeView

urlpatterns = [
    path('', IdnTableIcannModeView.as_view(), name='lgr_idn_icann_mode'),
]
