#! /bin/env python
# -*- coding: utf-8 -*-
"""
create - 
"""
import logging
import os
import re

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import FormView

from lgr_advanced.lgr_editor.forms import CreateLGRForm, ImportLGRForm
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.views import LGRViewMixin
from lgr_models.models import RzLgr

logger = logging.getLogger(__name__)

RE_SAFE_FILENAME = re.compile(r'[a-zA-Z0-9. _\-()]+')


class NewLGRView(LGRViewMixin, FormView):
    form_class = CreateLGRForm
    template_name = 'lgr_editor/new_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_id = ''

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'lgrs': self.session.list_lgr()
        })
        return ctx

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_id': self.lgr_id})

    def form_valid(self, form):
        self.lgr_id = form.cleaned_data['name']
        if self.lgr_id.endswith('.xml'):
            self.lgr_id = self.lgr_id.rsplit('.', 1)[0]
        self.lgr_id = slugify(self.lgr_id)

        if self.lgr_id in [lgr['name'] for lgr in self.session.list_lgr()]:
            logger.error("Import existing LGR")
            return render(self.request, 'lgr_editor/import_invalid.html',
                          context={'error': _(
                              "The LGR you have tried to create already exists in your working session. Please use a new name.")})

        self.session.new_lgr(self.lgr_id,
                             form.cleaned_data['unicode_version'],
                             form.cleaned_data['validating_repertoire'])
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
        self.lgr_id = ''
        self.lgr_names = [lgr['name'] for lgr in self.session.list_lgr()]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'lgrs': self.session.list_lgr()
        })
        return ctx

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_id': self.lgr_id})

    def form_valid(self, form):
        lgr_files = self.request.FILES.getlist('file')
        is_set = len(lgr_files) > 1
        validating_repertoire = form.cleaned_data['validating_repertoire']
        lgr_info_set = []
        for lgr_file in lgr_files:
            try:
                lgr_info = self._handle_lgr_file(lgr_file, validating_repertoire, is_set, lgr_info_set)
                lgr_info_set.append(lgr_info)
                self.lgr_id = lgr_info.name
            except ImportLGRView.LGRImportException as exc:
                return render(self.request, 'lgr_editor/import_invalid.html',
                              context={'error': exc.error})

        if is_set:
            try:
                set_name = form.cleaned_data['set_name']
                self.lgr_id = self._handle_set(lgr_info_set, set_name)
            except ImportLGRView.LGRImportException as exc:
                return render(self.request, 'lgr_editor/import_invalid.html',
                              context={'error': exc.error})

        return super().form_valid(form)

    def _handle_lgr_file(self, lgr_file, validating_repertoire: RzLgr, is_set, lgr_info_set):
        lgr_id = lgr_file.name
        if not RE_SAFE_FILENAME.match(lgr_id):
            raise SuspiciousOperation()
        if lgr_id.endswith('.xml'):
            lgr_id = lgr_id.rsplit('.', 1)[0]
        lgr_id = slugify(lgr_id)

        if not is_set and lgr_id in self.lgr_names:
            logger.error("Import existing LGR")
            raise ImportLGRView.LGRImportException(_("The LGR you have tried to import already exists in your working "
                                                     "session. Please rename it before importing it."))

        if is_set and lgr_id in [lgr.name for lgr in lgr_info_set]:
            logger.error("Import existing LGR in set")
            raise ImportLGRView.LGRImportException(_("The LGR you have tried to import already exists in your set. "
                                                     "Please rename it before importing it."))

        try:
            self.session.save_lgr(validating_repertoire.to_lgr_info(), validating_repertoire.name)
            lgr_info = self.session.open_lgr(lgr_id,
                                             lgr_file.read(),
                                             validating_repertoire=validating_repertoire.name,
                                             validate=True,
                                             from_set=is_set)
        except Exception as import_error:
            logger.exception("Input is not valid")
            raise ImportLGRView.LGRImportException(lgr_exception_to_text(import_error))

        return lgr_info

    def _handle_set(self, lgr_info_set, set_name):
        merged_id = slugify(set_name)
        if merged_id in self.lgr_names:
            logger.error("Import existing LGR set")
            raise ImportLGRView.LGRImportException(_("The LGR set name already exists. Please use another name."))

        try:
            merged_id = self.session.merge_set(lgr_info_set, set_name)
        except Exception as import_error:
            # remove imported LGRs, those that were already existing won't be erased
            logger.exception("Merge LGR from set is invalid")
            raise ImportLGRView.LGRImportException(lgr_exception_to_text(import_error))

        return merged_id


class ImportReferenceLGRView(LGRViewMixin, View):
    """
    Import a built-in LGR to user's session.
    """

    def get(self, request, *args, **kwargs):
        filename = self.kwargs['filename']
        if not RE_SAFE_FILENAME.match(filename):
            raise SuspiciousOperation()
        self.lgr_id = filename
        if self.lgr_id.endswith('.xml'):
            self.lgr_id = self.lgr_id.rsplit('.', 1)[0]
        self.lgr_id = slugify(self.lgr_id)
        with open(os.path.join(settings.LGR_STORAGE_LOCATION, filename + '.xml'), 'rb') as f:
            self.session.open_lgr(self.lgr_id, f.read())
        return redirect('codepoint_list', lgr_id=self.lgr_id)


class DeleteLGRView(LGRViewMixin, View):
    """
    Delete the selected LGR from session.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_id = self.kwargs['lgr_id']

    # TODO make that a post
    def get(self, request, *args, **kwargs):
        self.session.delete_lgr(self.lgr_id)
        return redirect('/')
