# -*- coding: utf-8 -*-
import os

from django.db import models


def get_upload_path(instance, filename):
    base_path = 'idn_table_review'
    if isinstance(instance, RzLgr):
        return os.path.join(base_path, 'rz_lgr', filename)
    if isinstance(instance, RefLgr):
        return os.path.join(base_path, 'reference_lgr', filename)
    if isinstance(instance, RzLgrMember):
        return os.path.join(base_path, 'rz_lgr', instance.rz_lgr.name, filename)


class LgrModel(models.Model):
    file = models.FileField(upload_to=get_upload_path)
    name = models.CharField(max_length=128)

    class Meta:
        ordering = ['name']
        abstract = True

    @property
    def filename(self):
        return os.path.basename(self.file.name)


class RzLgr(LgrModel):
    pass


class RefLgr(LgrModel):
    language_script = models.CharField(max_length=32, unique=True)


class RzLgrMember(LgrModel):
    rz_lgr = models.ForeignKey(to=RzLgr, on_delete=models.CASCADE, related_name='repository')
