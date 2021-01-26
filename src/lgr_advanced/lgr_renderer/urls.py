# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from lgr_web.converters import LgrSlugConverter
from . import views

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('<lgr:lgr_id>', views.LGRRendererView.as_view(), kwargs={'lgr_set_id': None}, name='lgr_render'),
    path('<lgr:lgr_set_id>/<lgr:lgr_id>', views.LGRRendererView.as_view(), name='lgr_render'),
]
