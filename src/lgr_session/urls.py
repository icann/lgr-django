from django.urls import path

from lgr_session.views import DeleteReportFileView, DownloadReportFileView

urlpatterns = [
    path('<storage:storage>/file/<int:pk>/dl/', DownloadReportFileView.as_view(), name='download_report_file'),
    path('<storage:storage>/<filename:report_id>/rm/', DeleteReportFileView.as_view(), name='delete_report_file'),
    path('<storage:storage>/file/<int:pk>/rm/', DeleteReportFileView.as_view(), name='delete_report_file'),
]
