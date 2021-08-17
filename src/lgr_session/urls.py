# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from lgr_web.converters import StorageTypeConverter, FileNameConverter
from .views import DownloadReportView, DeleteReportView

register_converter(StorageTypeConverter, 'storage')
register_converter(FileNameConverter, 'filename')

urlpatterns = [
    path('<storage:storage>/file/<int:pk>/dl/', DownloadReportView.as_view(), name='download_report'),
    path('<storage:storage>/<filename:report_id>/rm/', DeleteReportView.as_view(), name='delete_report'),
    path('<storage:storage>/file/<int:pk>/rm/', DeleteReportView.as_view(), name='delete_report'),
]
