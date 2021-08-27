# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from . import views
from .converters import LgrModelConverter

register_converter(LgrModelConverter, 'lgr_model')


urlpatterns = [
    path('<lgr_model:model>/<int:lgr_pk>', views.LGRRendererView.as_view(), name='lgr_render'),
]
