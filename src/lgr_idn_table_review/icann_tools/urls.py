# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from lgr_idn_table_review.icann_tools.views import (IdnTableIcannModeView,
                                                    IdnTableIcannListReports,
                                                    IdnTableIcannModeComplianceView)
from lgr_web.converters import FileNameConverter

register_converter(FileNameConverter, 'filename')

urlpatterns = [
    path('', IdnTableIcannModeView.as_view(), name='lgr_idn_icann_mode'),
    path('idna2008', IdnTableIcannModeComplianceView.as_view(), name='lgr_idn_icann_compliance'),
    path('report/<filename:report_id>', IdnTableIcannListReports.as_view(), name='lgr_idn_icann_reports'),
]
