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
import lgr_session.urls
from .views import LGRModesView, LGRSwitchModeView, LGRAboutView, LanguageAutocomplete

urlpatterns = [
    path('a/', include(lgr_advanced.urls.urlpatterns)),
    path('b/', include(lgr_basic.urls.urlpatterns)),
    path('r/', include(lgr_idn_table_review.urls.urlpatterns)),
    path('auth/', include(lgr_auth.urls.urlpatterns)),
    path('storage/', include(lgr_session.urls.urlpatterns)),

    # autocompletion
    path('language-autocomplete/', LanguageAutocomplete.as_view(), name='language-autocomplete'),

    path('i18n/', include('django.conf.urls.i18n')),

    path('about/', LGRAboutView.as_view(), name='about'),

    path('switch/', LGRSwitchModeView.as_view(), name='lgr_modes'),
    path('', LGRModesView.as_view(), name='lgr_home'),
]
