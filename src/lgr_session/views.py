# -*- coding: utf-8 -*-
from enum import Enum

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import Http404, FileResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View

from lgr_session.api import LGRStorage


class StorageType(Enum):
    TOOL = 'tool'
    IDN_REVIEW_USER_MODE = 'rev_usr'
    IDN_REVIEW_ICANN_MODE = 'rev_icann'


class LGRSessionView(LoginRequiredMixin, UserPassesTestMixin, View):

    def __storage_classes(self, klass=LGRStorage):
        subclasses = set()
        for subclass in klass.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(self.__storage_classes(subclass))
        return subclasses

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.report_id = self.kwargs.get('report_id')
        self.pk = self.kwargs.get('pk', None)
        self.next = request.GET.get('next', '/')
        storage_type = self.kwargs.get('storage')
        for subclass in self.__storage_classes():
            if not subclass.storage_model:
                continue
            if subclass.storage_model.storage_type == StorageType(storage_type):
                self.session = subclass(request.user)
                return
        raise Http404

    def test_func(self):
        return self.session.storage_can_read()


class DownloadReportView(LGRSessionView):

    def get(self, request, *args, **kwargs):
        try:
            report = self.session.storage_get_report_file(self.pk)
        except self.session.storage_model.DoesNotExist:
            messages.error(request, _('Unable to download file from report %(pk)s') %
                           {'pk': self.pk})
            return redirect(self.next)
        response = FileResponse(report.file)
        if 'display' not in self.request.GET:
            response['Content-Disposition'] = 'attachment; filename={}'.format(report.filename)
        return response


class DeleteReportView(LGRSessionView):

    # TODO make that a post
    def get(self, request, *args, **kwargs):
        if self.pk:
            self.session.storage_delete_report_file(self.pk)
        if self.report_id:
            self.session.storage_delete_report(self.report_id)
        return redirect(self.next)
