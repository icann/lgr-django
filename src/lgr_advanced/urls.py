"""
lgr_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information, please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.conf.urls import include
from django.urls import path

import lgr_advanced.lgr_editor.urls
import lgr_advanced.lgr_tools.urls
import lgr_advanced.lgr_validator.urls
from lgr_advanced.views import AdvancedModeView

urlpatterns = [
    path('editor/', include(lgr_advanced.lgr_editor.urls.urlpatterns)),
    path('validator/', include(lgr_advanced.lgr_validator.urls.urlpatterns)),
    path('tools/', include(lgr_advanced.lgr_tools.urls.urlpatterns)),
    path('', AdvancedModeView.as_view(), name='lgr_advanced_mode'),
]
