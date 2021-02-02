# -*- coding: utf-8 -*-
from enum import IntEnum, auto

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.utils.translation import ugettext_lazy as _


class LgrUserManager(BaseUserManager):
    """
    Custom LGR User Manager
    """

    def create_user(self, email, **kwargs):
        """
        Create a base user with email.
        """
        if not email:
            raise ValueError(_('Email is mandatory'))
        email = self.normalize_email(email)
        kwargs.setdefault('role', LgrRole.ICANN.value)
        password = kwargs.pop('password', None)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **kwargs):
        """
        Create an admin user with email and password.
        """
        user = self.create_user(email=email, password=password, role=LgrRole.ADMIN.value, **kwargs)
        user.save()
        return user


class LgrRole(IntEnum):
    ADMIN = auto()
    ICANN = auto()


class LgrUser(AbstractBaseUser):
    """
    Model of an User.
    """
    email = models.EmailField(unique=True,
                              help_text=_('Required. Valid email address'),
                              error_messages={
                                  'unique': _("An user with that email already exists."),
                              })
    role = models.PositiveSmallIntegerField(default=LgrRole.ICANN.value)

    # The username field will be the email address
    USERNAME_FIELD = 'email'

    # Define custom User manager class
    objects = LgrUserManager()
