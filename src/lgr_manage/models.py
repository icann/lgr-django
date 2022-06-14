#! /bin/env python
# -*- coding: utf-8 -*-
"""
models.py - 
"""
import os
from django.db import models

from lgr_auth.models import LgrUser
from lgr_models.models.lgr import LgrBaseModel
from lgr_models.models.report import LGRReport
from lgr_session.views import StorageType


class AdminReport(LGRReport):
    storage_type = StorageType.ADMIN

    @staticmethod
    def upload_path(instance, filename):
        return os.path.join(instance.storage, filename)
