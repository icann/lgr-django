# -*- coding: utf-8 -*-
"""
lgr_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
"""
from __future__ import unicode_literals

from django.conf.urls import include
from django.urls import path

import lgr_advanced.urls
import lgr_auth.urls
import lgr_basic.urls
import lgr_idn_table_review.urls
import lgr_manage.urls
import lgr_renderer.urls
import lgr_session.urls
import lgr_tasks.urls
import lgr_utils.urls
from .views import LGRModesView, LGRAboutView, LGRHelpView, LanguageAutocomplete

urlpatterns = [
    path('a/', include(lgr_advanced.urls.urlpatterns)),
    path('b/', include(lgr_basic.urls.urlpatterns)),
    path('r/', include(lgr_idn_table_review.urls.urlpatterns)),
    path('m/', include(lgr_manage.urls.urlpatterns)),
    path('auth/', include(lgr_auth.urls.urlpatterns)),
    path('storage/', include(lgr_session.urls.urlpatterns)),
    path('render/', include(lgr_renderer.urls.urlpatterns)),
    path('tasks/', include(lgr_tasks.urls.urlpatterns)),
    path('u/', include(lgr_utils.urls.urlpatterns)),

    # autocompletion
    path('language-autocomplete/', LanguageAutocomplete.as_view(), name='language-autocomplete'),

    path('i18n/', include('django.conf.urls.i18n')),

    path('about/', LGRAboutView.as_view(), name='about'),
    path('help/', LGRHelpView.as_view(), name='help'),

    path('', LGRModesView.as_view(), name='lgr_home'),
]
