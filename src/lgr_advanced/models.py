#! /bin/env python
# -*- coding: utf-8 -*-
"""
models.py - 
"""
import os
from io import BytesIO

from django.core.cache import cache
from django.core.files import File
from django.db import models

from lgr.core import LGR
from lgr.metadata import Metadata, Version
from lgr.parser.xml_serializer import serialize_lgr_xml
from lgr.tools.merge_set import merge_lgr_set
from lgr_utils import unidb
from lgr_models.models.lgr import LgrBaseModel
from lgr_models.models.report import LGRReport


# class MSR(LgrBaseModel):
#     pass


class RepertoireCacheMixin:
    repertoire_cache_key = 'repertoire'

    def get_repertoire_cache(self):
        cache.get(self._cache_key(self.repertoire_cache_key))

    def set_repertoire_cache(self, repertoire):
        cache.set(self._cache_key(self.repertoire_cache_key), repertoire, self.cache_timeout)

    def _clean_repertoire_cache(self):
        cache.delete(self._cache_key(self.repertoire_cache_key))

    def delete(self, *args, **kwargs):
        self._clean_repertoire_cache()
        return super().delete(*args, **kwargs)


class CommonLgrModel(LgrBaseModel):
    # validating_repertoire = models.ForeignKey(MSR, null=True, blank=True, on_delete=models.SET_NULL)
    validating_repertoire = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        abstract = True


class LgrModel(CommonLgrModel, RepertoireCacheMixin):

    @classmethod
    def new(cls, user, name, unicode_version, validating_repertoire_name):
        metadata = Metadata()
        metadata.version = Version('1')
        metadata.set_unicode_version(unicode_version)
        if name.endswith('.xml'):
            name = name.rsplit('.', 1)[0]
        lgr = LGR(name, metadata=metadata)
        lgr.unicode_database = unidb.manager.get_db_by_version(unicode_version)
        data = serialize_lgr_xml(lgr, pretty_print=True)
        lgr_object = cls.objects.create(file=File(BytesIO(data), name=f'{name}.xml'),
                                        name=name,
                                        owner=user,
                                        validating_repertoire=validating_repertoire_name)
        lgr_object._to_cache(lgr)
        return lgr_object

    def update(self, lgr, validate=False):
        filename = self.filename  # keep filename as file will be deleted
        data = self._parse_lgr_xml(lgr, validate=validate)
        self.file.delete(save=False)
        self.file = File(BytesIO(data), name=filename)
        self._to_cache(lgr)
        self._clean_repertoire_cache()
        self.save(update_fields=['file'])

    def is_set(self):
        try:
            return self.set_info is not None
        except LgrSetInfo.DoesNotExist:
            return False

    def embedded_lgrs(self):
        if self.is_set():
            return self.set_info.lgr_set.all()
        return []


class LgrSetInfo(models.Model):
    # need nullable as we need to create the set info, use it for set lgr models and merge then create the relation
    lgr = models.OneToOneField('LgrModel', null=True, on_delete=models.CASCADE, related_name='set_info')

    def merge(self, name):
        """
        Merge LGRs to build the set.

        :param name: The name of the LGR set
        :return: The LGR set merge id
        """
        merged_lgr = merge_lgr_set([l.to_lgr() for l in self.lgr_set.all()], name)
        data = serialize_lgr_xml(merged_lgr, pretty_print=True)
        return data


class SetLgrModel(CommonLgrModel, RepertoireCacheMixin):
    common = models.ForeignKey(LgrSetInfo, null=False, blank=False, on_delete=models.CASCADE, related_name='lgr_set')

    @staticmethod
    def upload_path(instance, filename):
        return os.path.join(f'user_{instance.owner.id}', f'set_info_{instance.common.id}', filename)
