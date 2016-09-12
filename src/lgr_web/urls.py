# -*- coding: utf-8 -*-
"""
lgr_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
"""
from __future__ import unicode_literals
from django.conf.urls import include, url
import lgr_editor.urls
import lgr_validator.urls
import lgr_tools.urls
from . import views

urlpatterns = [
    url(r'^editor/', include(lgr_editor.urls.urlpatterns)),
    url(r'^validator/', include(lgr_validator.urls.urlpatterns)),
    url(r'^tools/', include(lgr_tools.urls.urlpatterns)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^$', views.index, name='homepage'),
]
