# -*- coding: utf-8 -*-
from enum import Enum

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import SuspiciousOperation
from django.http import Http404, FileResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View

from lgr_advanced.api import LgrToolSession
from lgr_advanced.lgr_editor.views import RE_SAFE_FILENAME
from lgr_auth.models import LgrRole
from lgr_idn_table_review.icann.api import LgrIcannSession
from lgr_idn_table_review.tool.api import LgrIdnReviewSession


class StorageType(Enum):
    TOOL = 'tool'
    IDN_REVIEW_USER_MODE = 'rev_usr'
    IDN_REVIEW_ICANN_MODE = 'rev_icann'


class LgrSessionView(UserPassesTestMixin, View):

    def dispatch(self, request, *args, **kwargs):
        self.filename = self.kwargs.get('filename')
        if not RE_SAFE_FILENAME.match(self.filename):
            raise SuspiciousOperation()
        self.folder = self.kwargs.get('folder', None)
        if self.folder and not RE_SAFE_FILENAME.match(self.folder):
            raise SuspiciousOperation()
        self.next = request.GET.get('next', '/')
        storage_type = self.kwargs.get('storage')
        if StorageType(storage_type) == StorageType.TOOL:
            self.session = LgrToolSession(self.request)
        elif StorageType(storage_type) == StorageType.IDN_REVIEW_USER_MODE:
            self.session = LgrIdnReviewSession(request)
        elif StorageType(storage_type) == StorageType.IDN_REVIEW_ICANN_MODE:
            self.session = LgrIcannSession(request)
        else:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        storage_type = self.kwargs.get('storage')
        if StorageType(storage_type) == StorageType.IDN_REVIEW_ICANN_MODE:
            return self.request.user.is_authenticated and self.request.user.role in [LgrRole.ICANN.value,
                                                                                     LgrRole.ADMIN.value]
        return True


class DownloadFileView(LgrSessionView):

    def get(self, request, *args, **kwargs):
        try:
            res_file = self.session.storage_get_file(self.filename, subfolder=self.folder)
            if res_file is None:
                raise FileNotFoundError
        except FileNotFoundError:
            messages.error(request, _('Unable to download file %s') % self.filename)
            return redirect(self.next)
        response = FileResponse(res_file[0])
        if 'display' not in self.request.GET:
            response['Content-Disposition'] = 'attachment; filename={}'.format(self.filename)
        return response


class DeleteFileView(LgrSessionView):

    def get(self, request, *args, **kwargs):
        self.session.storage_delete_file(self.filename, subfolder=self.folder)
        return redirect(self.next)
