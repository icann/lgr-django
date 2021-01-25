# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, register_converter

from lgr_idn_table_review import views
from lgr_web.converters import LgrSlugConverter

register_converter(LgrSlugConverter, 'lgr')

urlpatterns = [
    path('tool/<lgr:lgr_id>', views.lgr_idn_table_review, name='lgr_idn_table_review'),
]
