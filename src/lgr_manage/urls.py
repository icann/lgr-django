# -*- coding: utf-8 -*-
from django.urls import path

from lgr_manage.views.idna import IDNAView, IDNADeleteView, IDNAIsActiveView
from lgr_manage.views.msr import MSRView, MSRDeleteView, MSRIsActiveView
from lgr_manage.views.reference_lgr import RefLgrView, RefLgrDeleteView, RefLgrIsActiveView
from lgr_manage.views.rz_lgr import (RzLgrView,
                                     RzLgrDeleteView,
                                     RzLgrIsActiveView)
from lgr_manage.views.settings import LgrSettingsView, LgrCalculateIndexes
from lgr_manage.views.users import LgrUserView, LgrUserDeleteView, LgrUserChangeStatusView, LgrUserAdminUpdateView

urlpatterns = [
    path('', RzLgrView.as_view(), name='lgr_admin_mode'),
    path('rz-lgr', RzLgrView.as_view(), name='lgr_admin_rz_lgr'),
    path('rz-lgr/<int:lgr_pk>/delete', RzLgrDeleteView.as_view(), name='lgr_admin_delete_rz_lgr'),
    path('rz-lgr/isactive', RzLgrIsActiveView.as_view(), name='lgr_admin_isactive_rz_lgr'),
    path('ref-lgr', RefLgrView.as_view(), name='lgr_admin_ref_lgr'),
    path('ref-lgr/<int:lgr_pk>/delete', RefLgrDeleteView.as_view(), name='lgr_admin_delete_ref_lgr'),
    path('ref-lgr/isactive', RefLgrIsActiveView.as_view(), name='lgr_admin_isactive_ref_lgr'),
    path('msr', MSRView.as_view(), name='lgr_admin_msr'),
    path('idna', IDNAView.as_view(), name='lgr_admin_idna'),
    path('idna/<int:lgr_pk>/delete', IDNADeleteView.as_view(), name='lgr_admin_delete_idna'),
    path('idna/isactive', IDNAIsActiveView.as_view(), name='lgr_admin_isactive_idna'),
    path('msr/<int:lgr_pk>/delete', MSRDeleteView.as_view(), name='lgr_admin_delete_msr'),
    path('msr/isactive', MSRIsActiveView.as_view(), name='lgr_admin_isactive_msr'),
    path('users', LgrUserView.as_view(), name='lgr_admin_user_management'),
    path('users/<int:user_pk>/update', LgrUserAdminUpdateView.as_view(), name='lgr_admin_update_user'),
    path('users/<int:user_pk>/delete', LgrUserDeleteView.as_view(), name='lgr_admin_delete_user'),
    path('users/<int:user_pk>/status', LgrUserChangeStatusView.as_view(), name='lgr_admin_change_user_status'),
    path('settings', LgrSettingsView.as_view(), name='lgr_admin_settings'),
    path('settings/indexes', LgrCalculateIndexes.as_view(), name='lgr_admin_calculate_indexes')
]
