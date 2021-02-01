# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import views
from django.urls import path

# patterns from django.contrib.auth.urls
urlpatterns = [
    path('login/', views.LoginView.as_view(template_name='lgr_auth/login.html'), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
