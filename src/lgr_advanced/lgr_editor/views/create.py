#! /bin/env python
# -*- coding: utf-8 -*-
"""
create - 
"""
import logging
import os
import re
from io import BytesIO

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import FormView

from lgr_advanced.lgr_editor.forms import CreateLGRForm, ImportLGRForm
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.models import LgrModel, SetLgrModel, LgrSetInfo
from lgr_advanced.views import LGRViewMixin

logger = logging.getLogger(__name__)

RE_SAFE_FILENAME = re.compile(r'[a-zA-Z0-9. _\-()]+')


class NewLGRView(LGRViewMixin, FormView):
    form_class = CreateLGRForm
    template_name = 'lgr_editor/new_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_pk = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'lgrs': LgrModel.objects.filter(owner=self.request.user)
        })
        return ctx

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_pk': self.lgr_pk})

    def form_valid(self, form):
        lgr_name = form.cleaned_data['name']
        if lgr_name.endswith('.xml'):
            lgr_name = lgr_name.rsplit('.', 1)[0]

        if LgrModel.objects.filter(owner=self.request.user, name=lgr_name).exists():
            logger.error("Import existing LGR")
            return render(self.request, 'lgr_editor/import_invalid.html',
                          context={'error': _("The LGR you have tried to create already exists in your working session. Please use a new name.")})

        lgr_object = LgrModel.new(self.request.user, lgr_name,
                                  form.cleaned_data['unicode_version'],
                                  form.cleaned_data['validating_repertoire'])
        self.lgr_pk = lgr_object.pk
        return super(NewLGRView, self).form_valid(form)


class ImportLGRView(LGRViewMixin, FormView):
    """
    Import an LGR from XML file supplied by user.
    """
    form_class = ImportLGRForm
    template_name = 'lgr_editor/import_form.html'

    class LGRImportException(BaseException):

        def __init__(self, error):
            self.error = error

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_pk = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'lgrs': LgrModel.objects.filter(owner=self.request.user)
        })
        return ctx

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_pk': self.lgr_pk})

    @transaction.atomic
    def form_valid(self, form):
        lgr_files = self.request.FILES.getlist('file')
        is_set = len(lgr_files) > 1
        validating_repertoire = form.cleaned_data['validating_repertoire']

        lgr_set_info = None
        if is_set:
            lgr_set_info = LgrSetInfo.objects.create()

        lgr_set = []
        for lgr_file in lgr_files:
            try:
                lgr_object = self._handle_lgr_file(lgr_file, validating_repertoire, lgr_set_info, lgr_set)
                lgr_set.append(lgr_object)
                self.lgr_pk = lgr_object.pk
            except ImportLGRView.LGRImportException as exc:
                return render(self.request, 'lgr_editor/import_invalid.html',
                              context={'error': exc.error})

        if is_set:
            try:
                set_name = form.cleaned_data['set_name']
                if LgrModel.objects.filter(owner=self.request.user, name=set_name).exists():
                    logger.error("Import existing LGR set name")
                    raise ImportLGRView.LGRImportException(
                        _("The LGR set name already exists. Please use another name."))
                try:
                    data = lgr_set_info.merge(set_name)
                except Exception as import_error:
                    logger.exception("Merge LGR from set is invalid")
                    raise ImportLGRView.LGRImportException(lgr_exception_to_text(import_error))
                lgr_object = LgrModel.objects.create(file=File(BytesIO(data), name=f'{set_name}.xml'),
                                                     owner=self.request.user,
                                                     name=set_name)
                lgr_set_info.lgr = lgr_object
                lgr_set_info.save()
                self.lgr_pk = lgr_object.pk
            except ImportLGRView.LGRImportException as exc:
                return render(self.request, 'lgr_editor/import_invalid.html',
                              context={'error': exc.error})

        return super().form_valid(form)

    def _handle_lgr_file(self, lgr_file, validating_repertoire, lgr_set_info, lgr_set):
        lgr_name = lgr_file.name
        if not RE_SAFE_FILENAME.match(lgr_name):
            raise SuspiciousOperation()
        if lgr_name.endswith('.xml'):
            lgr_name = lgr_name.rsplit('.', 1)[0]

        if not lgr_set_info and LgrModel.objects.filter(owner=self.request.user,
                                                        name=lgr_name).exists():
            logger.error("Import existing LGR")
            raise ImportLGRView.LGRImportException(_("The LGR you have tried to import already exists in your working "
                                                     "session. Please rename it before importing it."))

        if lgr_set_info and lgr_name in [lgr.name for lgr in lgr_set]:
            logger.error("Import existing LGR in set")
            raise ImportLGRView.LGRImportException(_("The LGR you have tried to import already exists in your set. "
                                                     "Please rename it before importing it."))

        try:
            if lgr_set_info:
                lgr_object = SetLgrModel.objects.create(owner=self.request.user,
                                                 name=lgr_name,
                                                 file=lgr_file,
                                                 validating_repertoire=validating_repertoire,
                                                 common=lgr_set_info)
            else:
                lgr_object = LgrModel.objects.create(owner=self.request.user,
                                              name=lgr_name,
                                              file=lgr_file,
                                              validating_repertoire=validating_repertoire)
        except Exception as import_error:
            logger.exception("Input is not valid")
            raise ImportLGRView.LGRImportException(lgr_exception_to_text(import_error))

        return lgr_object


class ImportReferenceLGRView(LGRViewMixin, View):
    """
    Import a built-in LGR to user's session.
    """

    def get(self, request, *args, **kwargs):
        filename = self.kwargs['filename']
        if not RE_SAFE_FILENAME.match(filename):
            raise SuspiciousOperation()
        lgr_name = filename
        if lgr_name.endswith('.xml'):
            lgr_name = lgr_name.rsplit('.', 1)[0]
        with open(os.path.join(settings.LGR_STORAGE_LOCATION, lgr_name + '.xml'), 'rb') as f:
            lgr_object = LgrModel.objects.create(owner=request.user,
                                                 file=File(f, name=f'{lgr_name}.xml'),
                                                 name=lgr_name)
            self.lgr_pk = lgr_object.pk
        return redirect('codepoint_list', lgr_pk=self.lgr_pk)


class DeleteLGRView(LGRViewMixin, View):
    """
    Delete the selected LGR from session.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_pk = self.kwargs['lgr_pk']

    # TODO make that a post
    def get(self, request, *args, **kwargs):
        LgrModel.objects.get(owner=request.user, pk=self.lgr_pk).delete()
        return redirect('/')
