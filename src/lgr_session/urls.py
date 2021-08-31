# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from lgr_web.converters import StorageTypeConverter, FileNameConverter
from .views import DownloadReportFileView, DeleteReportFileView

register_converter(StorageTypeConverter, 'storage')
register_converter(FileNameConverter, 'filename')

urlpatterns = [
    path('<storage:storage>/file/<int:pk>/dl/', DownloadReportFileView.as_view(), name='download_report_file'),
    path('<storage:storage>/<filename:report_id>/rm/', DeleteReportFileView.as_view(), name='delete_report_file'),
    path('<storage:storage>/file/<int:pk>/rm/', DeleteReportFileView.as_view(), name='delete_report_file'),
]
