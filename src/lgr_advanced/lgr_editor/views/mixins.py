#! /bin/env python
# -*- coding: utf-8 -*-
"""
mixins - 
"""
import logging
import typing

from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext_lazy as _

from lgr.core import LGR
from lgr_advanced.models import LgrModel, SetLgrModel
from lgr_advanced.views import LGRViewMixin
from lgr_models.models.lgr import LgrBaseModel

logger = logging.getLogger(__name__)


class LGRHandlingBaseMixin(LGRViewMixin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lgr_pk: int = None
        self.lgr_object: typing.Union[LgrModel, SetLgrModel] = None
        self.lgr: LGR = None
        self.model: LgrBaseModel = None
        self.validating_repertoire: LgrBaseModel = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_pk = self.kwargs['lgr_pk']
        self.model = self.kwargs.get('model', LgrModel)
        self.lgr_object = self.model.get_object(request.user, self.lgr_pk)
        if hasattr(self.lgr_object, 'validating_repertoire') and self.lgr_object.validating_repertoire:
            self.validating_repertoire = self.lgr_object.validating_repertoire
        self.lgr = self.lgr_object.to_lgr()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'lgr_pk': self.lgr_pk,
            'lgr_object': self.lgr_object,
            'lgr': self.lgr,
            'is_set': self.lgr_is_set_or_in_set(),
        })
        if self.lgr_is_in_set():
            ctx['lgr_set_object'] = self.lgr_object.common.lgr
            ctx['lgr_set'] = self.lgr_object.common.lgr.to_lgr()
        return ctx

    def update_lgr(self, validate=False):
        return self.lgr_object.update(self.lgr, validate=validate)

    def lgr_is_set_or_in_set(self):
        return self.lgr_is_in_set() or self.lgr_object.is_set()

    def lgr_is_in_set(self):
        return self.model == SetLgrModel


class LGREditMixin(LGRHandlingBaseMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.lgr_is_set_or_in_set():
            return HttpResponseBadRequest(_('Cannot edit LGR set'))
