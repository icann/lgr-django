# -*- coding: utf-8 -*-
from django.urls import path

from lgr_idn_table_review.admin.views.reference_lgr import RefLgrView, RefLgrDeleteView, DisplayRefLgrView
from lgr_idn_table_review.admin.views.rz_lgr import RzLgrView, RzLgrDeleteView, DisplayRzLgrView, DisplayRzLgrMemberView
from lgr_idn_table_review.admin.views.users import LgrUserView, LgrUserDeleteView

urlpatterns = [
    path('', RzLgrView.as_view(), name='lgr_idn_admin_mode'),
    path('rz-lgr', RzLgrView.as_view(), name='lgr_idn_admin_rz_lgr'),
    path('rz-lgr/<int:lgr_id>/delete', RzLgrDeleteView.as_view(), name='lgr_idn_admin_delete_rz_lgr'),
    path('rz-lgr/<int:lgr_id>', DisplayRzLgrView.as_view(), name='lgr_idn_admin_display_rz_lgr'),
    path('rz-lgr/<int:rz_lgr_id>/<int:lgr_id>', DisplayRzLgrMemberView.as_view(),
         name='lgr_idn_admin_display_rz_lgr_member'),
    path('ref-lgr', RefLgrView.as_view(), name='lgr_idn_admin_ref_lgr'),
    path('ref-lgr/<int:lgr_id>/delete', RefLgrDeleteView.as_view(), name='lgr_idn_admin_delete_ref_lgr'),
    path('ref-lgr/<int:lgr_id>', DisplayRefLgrView.as_view(), name='lgr_idn_admin_display_ref_lgr'),
    path('users', LgrUserView.as_view(), name='lgr_idn_admin_user_management'),
    path('users/<int:user_id>/delete', LgrUserDeleteView.as_view(), name='lgr_idn_admin_delete_user'),
]
