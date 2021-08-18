# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path

from . import views

urlpatterns = [
    path('<int:lgr_pk>', views.LGRRendererDbView.as_view(), name='lgr_render_from_db'),
    path('<int:lgr_pk>', views.LGRRendererView.as_view(), name='lgr_render'),
    path('set/<int:lgr_pk>', views.LGRRendererView.as_view(), kwargs={'in_set': True}, name='lgr_render_set'),
]
