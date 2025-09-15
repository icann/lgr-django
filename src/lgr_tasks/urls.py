from django.urls import path

from lgr_tasks.views import DeleteAllFinishedProcessesView, DeleteProcessView, ProcessListView

urlpatterns = [
    path('list', ProcessListView.as_view(), name='list_process'),
    path('<int:task_id>/delete', DeleteProcessView.as_view(), name='delete_process'),
    path('delete', DeleteAllFinishedProcessesView.as_view(), name='delete_finished'),
]
