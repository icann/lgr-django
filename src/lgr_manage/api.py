#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
from lgr_manage.models import AdminReport
from lgr_session.api import LGRReportStorage


class LGRAdminReportStorage(LGRReportStorage):
    storage_model = AdminReport

    def __init__(self, user=None):
        super().__init__(user, filter_on_user=False)

    def storage_can_read(self):
        return self.user.is_admin()
