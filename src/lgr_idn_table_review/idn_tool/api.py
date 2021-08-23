#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import logging

from lgr_idn_table_review.idn_tool.models import IdnReviewReport
from lgr_session.api import LGRStorage
from lgr_session.views import StorageType

logger = logging.getLogger(__name__)


class LGRIdnReviewStorage(LGRStorage):
    storage_model = IdnReviewReport
    storage_type = StorageType.IDN_REVIEW_USER_MODE
