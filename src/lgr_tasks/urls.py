# -*- coding: utf-8 -*-
from django.urls import path

from .views import ProcessListView, DeleteProcessView, DeleteAllFinishedProcessView

urlpatterns = [
    path('list', ProcessListView.as_view(), name='list_process'),
    path('<int:task_id>/delete', DeleteProcessView.as_view(), name='delete_process'),
    path('delete', DeleteAllFinishedProcessView.as_view(), name='delete_finished'),
]
