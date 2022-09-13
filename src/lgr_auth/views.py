#! /bin/env python
# -*- coding: utf-8 -*-
"""
views.py
"""
import logging
from enum import Enum

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, LoginView
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.views.generic import View, TemplateView

from lgr_auth.forms import UserForm
from lgr_auth.models import LgrUser

logger = logging.getLogger(__name__)


class LgrTokenAuthState(Enum):
    AUTHORIZE = 'authorize'
    EDIT = 'edit'


class LgrLoginView(LoginView):

    def dispatch(self, request, *args, **kwargs):
        ret = super().dispatch(request, *args, **kwargs)
        if settings.AUTH_METHOD == 'ICANN':
            return redirect(
                f'https://accounts-qa.icann.org/authorize'
                f'?client_id={settings.ICANN_AUTH_CLIENT_ID}'
                f'&redirect_uri={self.request.build_absolute_uri(reverse("icann_tokens"))}'
                f'&nonce={settings.ICANN_AUTH_NONCE}'
                f'&state={LgrTokenAuthState.AUTHORIZE.value}'
                f'&response_mode=form_post'
            )
        return ret


class LgrLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        ret = super().dispatch(request, *args, **kwargs)
        if settings.AUTH_METHOD == 'ICANN':
            return redirect('https://accounts-qa.icann.org')
        return ret


class LgrUserUpdateView(LoginRequiredMixin, UpdateView):
    model = LgrUser
    form_class = UserForm
    pk_url_kwarg = 'user_pk'
    template_name = 'lgr_auth/user_update.html'
    success_url_name = 'lgr_update_user'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['can_edit_role'] = self.request.user.is_admin()
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_edit'] = self.request.user.is_admin() or settings.AUTH_METHOD != 'ICANN'
        ctx['can_edit_icann_profile'] = settings.AUTH_METHOD == 'ICANN' and self.request.user == self.object
        return ctx

    def get_queryset(self):
        return LgrUser.objects.filter(pk=self.request.user.pk)

    def get_success_url(self):
        return reverse(self.success_url_name, kwargs={'user_pk': self.kwargs[self.pk_url_kwarg]})

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('User updated'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to update user'))
        return super().form_invalid(form)


@method_decorator(csrf_exempt, name='dispatch')
class TokenAuthenticateView(View):

    def post(self, request, *args, **kwargs):
        user = authenticate(request)
        if not user:
            return redirect('icann_login_failure')
        login(request, user)
        redirect_url = settings.LOGIN_REDIRECT_URL
        params = {}
        if user._lgr_state == LgrTokenAuthState.EDIT.value:
            redirect_url = 'lgr_update_user'
            params = {'user_pk': user.pk}
        return HttpResponseRedirect(resolve_url(redirect_url, **params))


class TokenAuthenticationFailureView(TemplateView):
    template_name = 'lgr_auth/token_failure.html'


class EditIcannProfileView(View):

    def get(self, request, *args, **kwargs):
        if settings.AUTH_METHOD != 'ICANN':
            return HttpResponseBadRequest(_('User is not logged with ICANN'))

        return redirect(
            f'https://accounts-qa.icann.org/account/edit'
            f'?client_id={settings.ICANN_AUTH_CLIENT_ID}'
            f'&redirect_uri={self.request.build_absolute_uri(reverse("icann_tokens"))}'
            f'&nonce={settings.ICANN_AUTH_NONCE}'
            f'&state={LgrTokenAuthState.EDIT.value}'
            f'&response_mode=form_post'
            f'&app_id={settings.ICANN_AUTH_APP_ID}'
        )
