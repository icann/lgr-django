# -*- coding: utf-8 -*-
from datetime import timedelta

from celery.states import STARTED, PENDING, REVOKED, SUCCESS
from django.db.models import Q
from django.utils import timezone

from lgr_tasks.models import LgrTaskModel
from lgr_web.celery_app import app


def get_task_info(user, task_id=None):
    """
    Try to get task information.

    This is actually pretty complicated as we cannot really know if task is still existing or not. So, if Celery
    is stopped, all lost pending task will remain in an unknown state.
    Therefore, we try to use reserved and scheduled tasks list to check for lost tasks but a new task may not be
    appearing in those lists neither.
    As we ordered our tasks, as soon as we found an active task we won't consider next tasks expired. We also wait for
    some time before considering a task as expired.
    """
    i = app.control.inspect()
    iactive = i.active()
    active = []
    if iactive:
        active = [t['id'] for t in sum(iactive.values() or [], [])]
    ireserved = i.reserved()
    ischeduled = i.scheduled()
    pending = []
    if ireserved:
        pending = [t['id'] for t in sum(ireserved.values() or [], [])]
    if ischeduled:
        pending += [t['id'] for t in sum(ischeduled.values() or [], [])]
    irevoked = i.revoked()
    revoked = []
    if irevoked:
        revoked = sum(irevoked.values() or [], [])
    tasks = []
    query = Q(user=user)
    found_active = False
    if task_id:
        query &= Q(pk=task_id)
    for task in LgrTaskModel.objects.filter(query).distinct():
        report = _get_report_instance(task.report)
        if report:
            status = SUCCESS
        else:
            result = app.AsyncResult(task.pk)
            status = result.status
            if status == PENDING:
                tid = task.pk
                if tid in active:
                    found_active = True
                    status = STARTED
                elif tid in revoked:
                    status = REVOKED
                elif tid not in pending and not found_active and \
                        timezone.now() - task.creation_date > timedelta(hours=1):
                    status = 'EXPIRED'

        task_info = {
            'id': task.pk,
            'app': task.app,
            'name': task.name,
            'creation_date': task.creation_date,
            'report': report,
            'status': status,
        }
        tasks.append(task_info)

    if task_id and tasks:
        return tasks[0]
    return tasks


def _get_report_instance(report):
    if not report:
        return
    for rel in report._meta.related_objects:
        # FIXME: need to recover real model to perform to_url in view
        #        As we do not have other relate_objects and few related models
        #        we can keep it like this but at one point we may better use
        #        https://django-polymorphic.readthedocs.io/en/stable/index.html instead
        try:
            report = getattr(report, rel.name)
        except Exception:
            continue
        else:
            break

    return report