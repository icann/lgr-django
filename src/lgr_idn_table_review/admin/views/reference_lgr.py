# -*- coding: utf-8 -*-

from lgr_idn_table_review.admin.models import ReferenceLgr
from lgr_idn_table_review.admin.views.common import BaseListAdminView


class ReferenceLgrListView(BaseListAdminView):
    model = ReferenceLgr
    template_name = 'ref_lgr.html'
