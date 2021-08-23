#! /bin/env python
# -*- coding: utf-8 -*-
"""
mixins - 
"""
import logging
import typing

from django.http import HttpResponseBadRequest

from lgr.core import LGR
from lgr_advanced.lgr_editor.repertoires import get_by_name
from lgr_advanced.models import LgrModel, SetLgrModel
from lgr_advanced.views import LGRViewMixin

logger = logging.getLogger(__name__)


class LGRHandlingBaseMixin(LGRViewMixin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lgr_pk: int = None
        self.lgr_object: typing.Union[LgrModel, SetLgrModel] = None
        self.lgr: LGR = None
        self.lgr_is_in_set = False
        self.validating_repertoire = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_pk = self.kwargs['lgr_pk']
        self.lgr_is_in_set = kwargs.get('in_set', False)
        if self.lgr_is_in_set:
            self.lgr_object = SetLgrModel.objects.get(owner=request.user, pk=self.lgr_pk)
        else:
            self.lgr_object = LgrModel.objects.get(owner=request.user, pk=self.lgr_pk)
        if self.lgr_object.validating_repertoire:
            self.validating_repertoire = get_by_name(self.lgr_object.validating_repertoire)
        self.lgr = self.lgr_object.to_lgr()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'lgr_pk': self.lgr_pk,
            'lgr_object': self.lgr_object,
            'lgr': self.lgr,
            'is_set': self.is_set_or_in_set()
        })
        if self.lgr_is_in_set:
            ctx['lgr_set_object'] = self.lgr_object.common.lgr
            ctx['lgr_set'] = self.lgr_object.common.lgr.to_lgr()
        return ctx

    def update_lgr(self, validate=False):
        return self.lgr_object.update(self.lgr, validate=validate)

    def is_set_or_in_set(self):
        return self.lgr_is_in_set or self.lgr_object.is_set()


class LGREditMixin(LGRHandlingBaseMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.is_set_or_in_set():
            return HttpResponseBadRequest('Cannot edit LGR set')
