# -*- coding: utf-8 -*-
"""
lgr_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
"""
from __future__ import unicode_literals

from django.conf.urls import include
from django.urls import path

import lgr_advanced.lgr_editor.urls
import lgr_advanced.lgr_renderer.urls
import lgr_advanced.lgr_tools.urls
import lgr_advanced.lgr_validator.urls
from .views import AdvancedModeView, LabelFormsView

urlpatterns = [
    path('editor/', include(lgr_advanced.lgr_editor.urls.urlpatterns)),
    path('validator/', include(lgr_advanced.lgr_validator.urls.urlpatterns)),
    path('tools/', include(lgr_advanced.lgr_tools.urls.urlpatterns)),
    path('render/', include(lgr_advanced.lgr_renderer.urls.urlpatterns)),
    path('label_forms/', LabelFormsView.as_view(), name='lgr_label_forms'),
    path('', AdvancedModeView.as_view(), name='lgr_advanced_mode'),
]
