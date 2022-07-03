#! /bin/env python
# -*- coding: utf-8 -*-
"""
views.py
"""
import logging

from django.contrib import messages
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView

from lgr_auth.forms import UserForm
from lgr_auth.models import LgrUser, LgrRole

logger = logging.getLogger(__name__)
from django.contrib.auth.mixins import LoginRequiredMixin


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
