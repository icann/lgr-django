#! /bin/env python
# -*- coding: utf-8 -*-
import os

from django.db import models
from django.urls import reverse

from lgr_auth.models import LgrUser


def get_upload_path(instance, filename):
    # if you need to use LGRReport in migration, this won't work as historical models don't include method.
    # See https://docs.djangoproject.com/en/3.1/topics/migrations/#historical-models
    # If you need this in a migration, define the method in the migration and set it to the historical model.
    return os.path.join('reports', instance.upload_path(instance, filename))


class LGRReport(models.Model):
    file = models.FileField(upload_to=get_upload_path)
    report_id = models.CharField(max_length=256)
    owner = models.ForeignKey(to=LgrUser, on_delete=models.CASCADE, related_name='+')
    storage_type = None

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def storage(self):
        return self.storage_type.value

    @staticmethod
    def upload_path(instance, filename):
        return os.path.join(instance.storage, f'user_{instance.owner.id}', filename)

    def to_url(self):
        return reverse('download_report_file', kwargs={'storage': self.storage, 'pk': self.pk})

    def delete_url(self):
        return reverse('delete_report_file', kwargs={'storage': self.storage, 'pk': self.pk})

