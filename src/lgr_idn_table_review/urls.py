# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, include

import lgr_idn_table_review.icann_tools.urls
import lgr_idn_table_review.idn_tool.urls

urlpatterns = [
    path('icann/', include(lgr_idn_table_review.icann_tools.urls.urlpatterns)),
    path('tool/', include(lgr_idn_table_review.idn_tool.urls.urlpatterns)),
]
