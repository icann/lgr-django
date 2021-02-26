# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path, include

import lgr_idn_table_review.idn_admin.urls
import lgr_idn_table_review.icann.urls
import lgr_idn_table_review.tool.urls

urlpatterns = [
    path('admin/', include(lgr_idn_table_review.idn_admin.urls.urlpatterns)),
    path('icann/', include(lgr_idn_table_review.icann.urls.urlpatterns)),
    path('tool/', include(lgr_idn_table_review.tool.urls.urlpatterns)),
]
