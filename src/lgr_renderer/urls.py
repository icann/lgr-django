# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from . import views
from lgr_utils.converters import LgrModelConverter

register_converter(LgrModelConverter, 'lgr_model')


urlpatterns = [
    path('html/<lgr_model:model>/<int:lgr_pk>', views.LGRRendererView.as_view(), name='lgr_render'),
    path('file/<lgr_model:model>/<int:lgr_pk>', views.LGRDisplayView.as_view(), name='lgr_display'),
    path('dl/<lgr_model:model>/<int:lgr_pk>', views.LGRDisplayView.as_view(), name='lgr_download',
         kwargs={'force_download': True}),
]
