#! /bin/env python
# -*- coding: utf-8 -*-
"""
models.py - 
"""
import os

from django.db import models
from django.urls import reverse

from lgr.parser.heuristic_parser import HeuristicParser
from lgr_models.models.lgr import LgrBaseModel
from lgr_models.models.report import LGRReport
from lgr_session.views import StorageType


class IdnReviewReport(LGRReport):
    storage_type = StorageType.IDN_REVIEW_USER_MODE

    @staticmethod
    def upload_path(instance, filename):
        return os.path.join(instance.storage, f'user_{instance.owner.id}', instance.report_id, filename)


class IdnTable(LgrBaseModel):
    lgr_parser = HeuristicParser

    report_id = models.CharField(max_length=256)

    def dl_url(self):
        return reverse('lgr_review_display_idn_table', kwargs={'lgr_pk': self.pk})
