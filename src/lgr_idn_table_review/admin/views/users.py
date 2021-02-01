# -*- coding: utf-8 -*-

from lgr_auth.models import LgrUser
from lgr_idn_table_review.admin.views.common import BaseListAdminView


class UserListView(BaseListAdminView):
    model = LgrUser
    template_name = 'user_management.html'
