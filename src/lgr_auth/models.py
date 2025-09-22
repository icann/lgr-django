from enum import Enum

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from lgr_auth.validators import ua_validate_email


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
        kwargs.setdefault('role', LgrRole.USER.value)
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


class LgrRole(Enum):
    USER = 'User'
    ICANN = 'ICANN'
    ADMIN = 'Admin'


class UAEmailField(models.EmailField):
    default_validators = [ua_validate_email]

    def formfield(self, **kwargs):
        from lgr_auth import forms

        return super().formfield(**{
            'form_class': forms.UAEmailField,
            **kwargs,
        })


class LgrUser(AbstractBaseUser):
    """
    Model of a User.
    """
    email = UAEmailField(unique=True,
                         help_text=_('Required. Valid email address'),
                         error_messages={
                             'unique': _("An user with that email already exists."),
                         },
                         max_length=100)
    role = models.CharField(max_length=16, choices=((r.value, r.value) for r in LgrRole), null=False,
                            default=LgrRole.USER.value)
    first_name = models.CharField(_('first name'), max_length=50, blank=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    icann_username = models.CharField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['email']

    # The username field will be the email address
    USERNAME_FIELD = 'email'

    # Define custom User manager class
    objects = LgrUserManager()

    def is_icann(self):
        return self.role in (LgrRole.ICANN.value, LgrRole.ADMIN.value)

    def is_admin(self):
        return self.role == LgrRole.ADMIN.value

    def enable(self, enable):
        self.is_active = enable
        self.save(update_fields=['is_active'])

    def enabled(self):
        return self.is_active

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
