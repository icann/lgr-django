#! /bin/env python
# -*- coding: utf-8 -*-
"""
models.py - 
"""
import os
from io import BytesIO

from django.core.files import File
from django.db import models

from lgr.core import LGR
from lgr.metadata import Metadata, Version
from lgr.parser.heuristic_parser import HeuristicParser
from lgr_models.models.lgr import LgrBaseModel
from lgr_models.models.report import LGRReport
from lgr_session.views import StorageType


class IdnReviewIcannReport(LGRReport):
    storage_type = StorageType.IDN_REVIEW_ICANN_MODE

    @staticmethod
    def upload_path(instance, filename):
        return os.path.join(instance.storage, instance.report_id, filename)


class IANAIdnTable(LgrBaseModel):
    """
    Model for a IANA IDN table, not meant to be saved in the database
    """
    lgr_parser = HeuristicParser

    url = models.URLField()
    date = models.DateField()
    lang_script = models.CharField(max_length=16)
    version = models.DecimalField(max_digits=2, decimal_places=1)

    class Meta:
        managed = False  # do not manage this model, this is only used to create objects that won't be saved in the DB
        # unique_together = ['url', 'date']

    def _parse(self, validate, with_unidb) -> LGR:
        lgr = super(IANAIdnTable, self)._parse(validate, with_unidb)
        meta: Metadata = lgr.metadata
        if self.date and not meta.date:
            meta.set_date(self.date.strftime('%Y-%m-%d'), force=True)
        if not meta.languages:
            meta.add_language(self.lang_script, force=True)
        if not meta.version:
            meta.version = Version(self.version)

        return lgr

    @staticmethod
    def upload_path(instance, filename):
        raise RuntimeError

    def save(self, *args, **kwargs):
        raise RuntimeError

    @classmethod
    def from_lgr(cls, owner, lgr, name=None, validate=False, **kwargs):
        name = name or lgr.name
        if name.endswith('.xml') or name.endswith('.txt'):
            name = os.path.splitext(name)[0]
        data = cls._parse_lgr_xml(lgr, validate=validate)

        file = File(BytesIO(data), name=f'{name}.xml')
        lgr_object = cls(owner=owner,
                         name=name,
                         file=file,
                         **kwargs)
        return lgr_object

    def _to_cache(self, lgr: LGR):
        return

    def _from_cache(self) -> LGR:
        return None

    def display_url(self):
        return self.url
