#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import QuerySet

from lgr_web import settings


class UnicodeVersion(models.Model):
    version = models.CharField(max_length=255, unique=True)
    activated = models.BooleanField(default=True)

    def __str__(self):
        return self.version

    @classmethod
    def default(cls) -> 'UnicodeVersion':
        if hasattr(settings, 'DEFAULT_UNICODE_VERSION') and cls.get_activated().filter(
                version=settings.DEFAULT_UNICODE_VERSION).exists():
            return cls.get_activated().get(version=settings.DEFAULT_UNICODE_VERSION)
        return cls.get_activated().first()

    @classmethod
    def all(cls) -> QuerySet['UnicodeVersion']:
        supported_versions = set(settings.SUPPORTED_UNICODE_VERSIONS).intersection(
            settings.UNICODE_DATABASES.keys())
        return UnicodeVersion.objects.filter(version__in=supported_versions)

    @classmethod
    def get_activated(cls) -> QuerySet['UnicodeVersion']:
        return cls.all().filter(activated=True)
