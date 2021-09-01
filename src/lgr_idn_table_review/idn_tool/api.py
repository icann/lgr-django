#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import logging
from datetime import datetime

from django.core.files import File

from lgr_idn_table_review.idn_tool.models import IdnReviewReport, IdnTable
from lgr_session.api import LGRStorage

logger = logging.getLogger(__name__)


class LGRIdnReviewApi(LGRStorage):
    storage_model = IdnReviewReport
    lgr_model = IdnTable

    @staticmethod
    def generate_report_id():
        return datetime.now().strftime('%Y-%m-%d-%H%M%S.%f')

    def lgr_queryset(self):
        return self.lgr_model.objects.filter(owner=self.user)

    def create_lgr(self, file, name, report_id):
        return IdnTable.objects.create(file=File(file),
                                       name=name,
                                       owner=self.user,
                                       report_id=report_id)

    def get_lgrs_in_report(self, report_id):
        return self.lgr_queryset().filter(report_id=report_id)

    def delete_report(self, report_id):
        self.storage_delete_report(report_id)
        self.get_lgrs_in_report(report_id).delete()
