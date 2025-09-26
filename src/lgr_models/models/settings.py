#! /bin/env python
# -*- coding: utf-8 -*-
from django.core.validators import MinValueValidator
from django.db import models


class LGRSettings(models.Model):
    variant_calculation_limit = models.PositiveIntegerField(validators=[MinValueValidator(2)])
    variant_calculation_max = models.PositiveIntegerField(validators=[MinValueValidator(3)])
    variant_calculation_abort = models.PositiveIntegerField(validators=[MinValueValidator(4)])
    report_expiration_delay = models.PositiveIntegerField()
    report_expiration_last_run = models.DateTimeField()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        exists = LGRSettings.objects.all().exists()
        if exists and self.pk is None or self.pk != 1:
            # only save one instance of settings
            raise BaseException('You can only use one instance of settings')
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
