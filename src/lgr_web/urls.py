# -*- coding: utf-8 -*-
"""
lgr_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
"""
from __future__ import unicode_literals

from django.conf.urls import include
from django.urls import path

import lgr_basic.urls
import lgr_editor.urls
import lgr_idn_table_review.urls
import lgr_renderer.urls
import lgr_tools.urls
import lgr_validator.urls
from . import views

urlpatterns = [
    path('editor/', include(lgr_editor.urls.urlpatterns)),
    path('validator/', include(lgr_validator.urls.urlpatterns)),
    path('tools/', include(lgr_tools.urls.urlpatterns)),
    path('render/', include(lgr_renderer.urls.urlpatterns)),
    path('basic/', include(lgr_basic.urls.urlpatterns)),
    path('review/', include(lgr_idn_table_review.urls.urlpatterns)),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', views.index, name='homepage'),
]
