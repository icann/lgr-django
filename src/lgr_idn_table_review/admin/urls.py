# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from lgr_idn_table_review.admin.views.reference_lgr import ReferenceLgrListView
from lgr_idn_table_review.admin.views.rz_lgr import RzLgrView, RzLgrDeleteView, DisplayRzLgrView, DisplayRzLgrMemberView
from lgr_idn_table_review.admin.views.users import UserListView
from lgr_web.converters import LgrSlugConverter

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('', RzLgrView.as_view(), name='lgr_idn_admin_mode'),
    path('rz-lgr', RzLgrView.as_view(), name='lgr_idn_admin_rz_lgr'),
    path('rz-lgr/<lgr:lgr_id>/delete', RzLgrDeleteView.as_view(), name='lgr_idn_admin_delete_rz_lgr'),
    path('ref-lgr', ReferenceLgrListView.as_view(), name='lgr_idn_admin_ref_lgr'),
    path('rz-lgr/<lgr:lgr_id>', DisplayRzLgrView.as_view(), name='lgr_idn_admin_display_rz_lgr'),
    path('rz-lgr/repo/<lgr:lgr_id>', DisplayRzLgrMemberView.as_view(), name='lgr_idn_admin_display_rz_lgr_member'),
    path('users', UserListView.as_view(), name='lgr_idn_admin_user_management'),
]
