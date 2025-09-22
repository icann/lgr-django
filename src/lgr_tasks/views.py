import logging

from celery.states import FAILURE, PENDING, RETRY, REVOKED, SUCCESS
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from lgr_tasks.api import get_task_info
from lgr_tasks.models import LgrTaskModel
from lgr_utils.views import safe_next_redirect_url
from lgr_web.celery_app import app

logger = logging.getLogger(__name__)


class ProcessListView(LoginRequiredMixin, TemplateView):
    template_name = 'lgr_tasks/process_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ctx['tasks'] = reversed(get_task_info(self.request.user))
        except:
            messages.error(self.request, _('Unable to retrieve the list of tasks.'))
        return ctx


class DeleteProcessView(LoginRequiredMixin, SingleObjectMixin, View):
    pk_url_kwarg = 'task_id'
    model = LgrTaskModel

    def post(self, request, *args, **kwargs):
        task: LgrTaskModel = self.get_object()
        try:
            task_info = get_task_info(request.user, task.pk)
            if not task_info:
                raise BaseException
        except:
            messages.error(self.request, _('Failed to delete %s.') % task.name)
            return redirect(safe_next_redirect_url(request, '/'))

        if task_info and task_info['status'] in [PENDING, RETRY]:
            # never set terminate=True as this will kill the worker.
            # That's why we don't allow deleting an active task
            app.control.revoke(task.pk, terminate=False)
            messages.info(self.request, _('Task %s has been revoked.') % task.name)
        else:
            LgrTaskModel.objects.filter(pk=task.pk).delete()
            messages.info(self.request, _('Task %s has been removed.') % task.name)

        return redirect('list_process')


class DeleteAllFinishedProcessesView(LoginRequiredMixin, MultipleObjectMixin, View):
    model = LgrTaskModel

    def get_queryset(self):
        queryset = super().get_queryset()
        try:
            tasks_info = get_task_info(self.request.user)
        except:
            messages.error(self.request, _('Failed to retrieve completed tasks.'))
            return queryset.none()

        return queryset.filter(
            pk__in=[t['id'] for t in tasks_info if t['status'] in [SUCCESS, FAILURE, REVOKED, 'EXPIRED']])

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            messages.info(self.request, _('Completed tasks have been cleaned.'))
            queryset.delete()

        return redirect('list_process')
