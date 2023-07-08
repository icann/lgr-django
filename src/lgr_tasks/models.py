# -*- coding: utf-8 -*-
from django.db import models

from lgr_auth.models import LgrUser
from lgr_models.models.report import LGRReport


class LgrTaskModel(models.Model):
    app = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    creation_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(to=LgrUser, on_delete=models.CASCADE, related_name='+')
    report = models.ForeignKey(to=LGRReport, on_delete=models.CASCADE, related_name='+', blank=True, null=True)

    class Meta:
        ordering = ['-creation_date']

    def __str__(self):
        return self.name
