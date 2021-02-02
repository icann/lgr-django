# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import views
from django.urls import path

# patterns from django.contrib.auth.urls
from lgr_auth.forms import LgrPasswordResetForm

urlpatterns = [
    path('login/', views.LoginView.as_view(template_name='lgr_auth/login.html'), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('password_reset/',
         views.PasswordResetView.as_view(template_name='lgr_auth/password_reset_form.html',
                                         email_template_name='lgr_auth/password_reset_email.html',
                                         subject_template_name='lgr_auth/password_reset_subject.txt',
                                         form_class=LgrPasswordResetForm),
         name='password_reset'),
    path('password_reset/done/',
         views.PasswordResetDoneView.as_view(template_name='lgr_auth/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         views.PasswordResetConfirmView.as_view(template_name='lgr_auth/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         views.PasswordResetCompleteView.as_view(template_name='lgr_auth/password_reset_complete.html'),
         name='password_reset_complete'),
]
