# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import views
from django.urls import path

from lgr_auth.forms import LgrPasswordResetForm
from lgr_auth.views import (LgrUserUpdateView,
                            LgrLoginView,
                            LgrLogoutView,
                            TokenAuthenticateView,
                            TokenAuthenticationFailureView,
                            EditIcannProfileView)

urlpatterns = [
    path('login/', LgrLoginView.as_view(template_name='lgr_auth/login.html'), name='login'),
    path('logout/', LgrLogoutView.as_view(), name='logout'),
    path('users/<int:user_pk>', LgrUserUpdateView.as_view(), name='lgr_update_user'),
]
if settings.AUTH_METHOD == 'ICANN':
    urlpatterns += [
        path('icann/tokens', TokenAuthenticateView.as_view(), name='icann_tokens'),
        path('icann/tokens/failure', TokenAuthenticationFailureView.as_view(), name='icann_login_failure'),
        path('icann/edit', EditIcannProfileView.as_view(), name='icann_update_user'),

    ]
else:
    urlpatterns += [
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
