from django.urls import include, path

urlpatterns = [
    path('icann/', include('lgr_idn_table_review.icann_tools.urls')),
    path('tool/', include('lgr_idn_table_review.idn_tool.urls')),
]
