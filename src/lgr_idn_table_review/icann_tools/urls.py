from django.urls import path

from lgr_idn_table_review.icann_tools.views import (
    IdnTableIcannListReports,
    IdnTableIcannModeComplianceView,
    IdnTableIcannModeView)

urlpatterns = [
    path('', IdnTableIcannModeView.as_view(), name='lgr_idn_icann_mode'),
    path('idna2008', IdnTableIcannModeComplianceView.as_view(), name='lgr_idn_icann_compliance'),
    path('report/<filename:report_id>', IdnTableIcannListReports.as_view(), name='lgr_idn_icann_reports'),
]
