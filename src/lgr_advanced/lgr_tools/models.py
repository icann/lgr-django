#! /bin/env python
# -*- coding: utf-8 -*-
from lgr_models.models.report import LGRReport
from lgr_session.views import StorageType


class LGRToolReport(LGRReport):
    storage_type = StorageType.TOOL