#! /bin/env python
# -*- coding: utf-8 -*-
"""
models.py - 
"""
import os

from lgr_models.models.report import LGRReport
from lgr_session.views import StorageType


class IdnReviewIcannReport(LGRReport):
    storage_type = StorageType.IDN_REVIEW_ICANN_MODE

    @staticmethod
    def upload_path(instance, filename):
        return os.path.join(instance.storage, instance.report_id, filename)
