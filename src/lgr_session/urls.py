# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from lgr_web.converters import (FileNameConverter, StorageTypeConverter)
from .views import DownloadFileView, DeleteFileView

register_converter(FileNameConverter, 'filename')
register_converter(StorageTypeConverter, 'storage')

urlpatterns = [
    path('<storage:storage>/<filename:filename>/dl/', DownloadFileView.as_view(), name='download_file'),
    path('<storage:storage><filename:filename>/rm/', DeleteFileView.as_view(), name='delete_file'),
]
