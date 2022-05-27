# -*- coding: utf-8 -*-
import logging

from celery.states import PENDING, RETRY, REVOKED, FAILURE, SUCCESS
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from lgr_tasks.api import get_task_info
from lgr_tasks.models import LgrTaskModel
from lgr_web.celery_app import app

logger = logging.getLogger(__name__)


class ProcessListView(LoginRequiredMixin, TemplateView):
    template_name = 'lgr_tasks/process_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tasks'] = get_task_info(self.request.user)
        return ctx


class DeleteProcessView(LoginRequiredMixin, SingleObjectMixin, View):
    pk_url_kwarg = 'task_id'
    model = LgrTaskModel

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        task_info = get_task_info(request.user, task.pk)
        if not task_info:
            logger.error('Cannot retrieve task to delete')
        if task_info and task_info['status'] in [PENDING, RETRY]:
            # never set terminate=True as this will kill the worker.
            # That's why we don't allow deleting an active task
            app.control.revoke(task.pk, terminate=False)
        else:
            LgrTaskModel.objects.filter(pk=task.pk).delete()

        return redirect(request.GET.get('next', '/'))


class DeleteAllFinishedProcessView(LoginRequiredMixin, MultipleObjectMixin, View):
    model = LgrTaskModel

    def get_queryset(self):
        queryset = super().get_queryset()
        tasks_info = get_task_info(self.request.user)
        return queryset.filter(pk__in=[t['id'] for t in tasks_info if t['status'] in [SUCCESS, FAILURE, REVOKED,
                                                                                      'EXPIRED']])

    def post(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return redirect(request.GET.get('next', '/'))
