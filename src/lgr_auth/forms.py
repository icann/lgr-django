# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.forms import ModelForm

from lgr_auth.models import LgrUser


class LgrPasswordResetForm(PasswordResetForm):
    """
    Subclass PasswordResetForm to remove condition on user's is_active.
    """

    def get_users(self, email):
        return get_user_model()._default_manager.filter(email__iexact=email)


class UserForm(ModelForm):
    class Meta:
        model = LgrUser
        fields = ['first_name', 'last_name', 'email', 'role']