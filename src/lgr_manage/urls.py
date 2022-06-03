# -*- coding: utf-8 -*-
from django.urls import path

from lgr_manage.views.msr import MSRView, MSRDeleteView, DisplayMSRView, MSRIsActiveView
from lgr_manage.views.reference_lgr import RefLgrView, RefLgrDeleteView, DisplayRefLgrView
from lgr_manage.views.rz_lgr import (RzLgrView,
                                     RzLgrDeleteView,
                                     DisplayRzLgrView,
                                     DisplayRzLgrMemberView,
                                     RzLgrIsActiveView)
from lgr_manage.views.settings import LgrSettingsView
# from lgr_manage.views.unicode_versions import (LgrUnicodeVersionUpdateView,
#                                                LgrUnicodeVersionsListView,
#                                                LgrUnicodeVersionCreateView)
from lgr_manage.views.users import LgrUserView, LgrUserDeleteView, LgrUserChangeStatusView, LgrUserAdminUpdateView

urlpatterns = [
    path('', RzLgrView.as_view(), name='lgr_admin_mode'),
    path('rz-lgr', RzLgrView.as_view(), name='lgr_admin_rz_lgr'),
    path('rz-lgr/<int:lgr_pk>/delete', RzLgrDeleteView.as_view(), name='lgr_admin_delete_rz_lgr'),
    path('rz-lgr/<int:lgr_pk>', DisplayRzLgrView.as_view(), name='lgr_admin_display_rz_lgr'),
    path('rz-lgr/<int:rz_lgr_pk>/<int:lgr_pk>', DisplayRzLgrMemberView.as_view(),
         name='lgr_admin_display_rz_lgr_member'),
    path('rz-lgr/isactive', RzLgrIsActiveView.as_view(), name='lgr_admin_isactive_rz_lgr'),
    path('ref-lgr', RefLgrView.as_view(), name='lgr_admin_ref_lgr'),
    path('ref-lgr/<int:lgr_pk>/delete', RefLgrDeleteView.as_view(), name='lgr_admin_delete_ref_lgr'),
    path('ref-lgr/<int:lgr_pk>', DisplayRefLgrView.as_view(), name='lgr_admin_display_ref_lgr'),
    path('msr', MSRView.as_view(), name='lgr_admin_msr'),
    path('msr/<int:lgr_pk>/delete', MSRDeleteView.as_view(), name='lgr_admin_delete_msr'),
    path('msr/<int:lgr_pk>', DisplayMSRView.as_view(), name='lgr_admin_display_msr'),
    path('msr/isactive', MSRIsActiveView.as_view(), name='lgr_admin_isactive_msr'),
    path('users', LgrUserView.as_view(), name='lgr_admin_user_management'),
    path('users/<int:user_pk>/update', LgrUserAdminUpdateView.as_view(), name='lgr_admin_update_user'),
    path('users/<int:user_pk>/delete', LgrUserDeleteView.as_view(), name='lgr_admin_delete_user'),
    path('users/<int:user_pk>/status', LgrUserChangeStatusView.as_view(), name='lgr_admin_change_user_status'),
    # path('unicode-versions', LgrUnicodeVersionsListView.as_view(), name='lgr_admin_unicode_versions'),
    # path('unicode-versions/<int:pk>/update', LgrUnicodeVersionUpdateView.as_view(),
    #      name='lgr_admin_unicode_version_update'),
    # path('unicode-versions/create', LgrUnicodeVersionCreateView.as_view(), name='lgr_admin_create_unicode_version'),
    path('settings', LgrSettingsView.as_view(), name='lgr_admin_settings')
]
