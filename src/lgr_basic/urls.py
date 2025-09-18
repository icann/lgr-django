# -*- coding: utf-8 -*-
from django.urls import path

from lgr_basic.views import BasicModeView

urlpatterns = [
    path('', BasicModeView.as_view(), name='lgr_basic_mode'),
]
