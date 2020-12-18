# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from lgr_idn_table_review import views

urlpatterns = [
    url(r'^tool/(?P<lgr_id>[\w\_\-\.]+)?$',
        views.lgr_idn_table_review,
        name='lgr_idn_table_review'),
]
