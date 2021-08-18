# -*- coding: utf-8 -*-
import os

from django.db import models
from lgr.core import LGR

from lgr.parser.xml_parser import XMLParser
from lgr.utils import tag_to_language_script

from lgr_advanced.api import LGRInfo


def get_upload_path(instance, filename):
    base_path = 'idn_table_review'
    # need to test on object_name because instance may not be a real object instance if called in a migration
    if instance._meta.object_name == 'RzLgr':
        return os.path.join(base_path, 'rz_lgr', filename)
    if instance._meta.object_name == 'RefLgr':
        return os.path.join(base_path, 'reference_lgr', filename)
    if instance._meta.object_name == 'RzLgrMember':
        return os.path.join(base_path, 'rz_lgr', instance.rz_lgr.name, filename)


class LgrModel(models.Model):
    file = models.FileField(upload_to=get_upload_path)
    name = models.CharField(max_length=128, unique=True)

    class Meta:
        ordering = ['name']
        abstract = True

    @property
    def filename(self):
        return os.path.basename(self.file.name)


class RzLgr(LgrModel):
    def __str__(self):
        return u'{0}'.format(self.name)

    def to_lgr_info(self) -> LGRInfo:
        self.file.seek(0)
        return LGRInfo.from_dict(
            {
                'name': self.name,
                'xml': self.file.read(),
                'lgr': LGR(self.name),
                'validate': False
            })


class RefLgr(LgrModel):
    language_script = models.CharField(max_length=32, unique=True)
    language = models.CharField(max_length=8, blank=True)
    script = models.CharField(max_length=8, blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.language, self.script = tag_to_language_script(self.language_script)
        super().save(force_insert, force_update, using, update_fields)


class RzLgrMember(LgrModel):
    rz_lgr = models.ForeignKey(to=RzLgr, on_delete=models.CASCADE, related_name='repository')
    language = models.CharField(max_length=8)
    script = models.CharField(max_length=8)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        lgr_parser = XMLParser(self.file.path)
        lgr = lgr_parser.parse_document()
        self.language, self.script = tag_to_language_script(lgr.metadata.languages[0])
        super().save(force_insert=False, force_update=True, using=using, update_fields=['language', 'script'])


