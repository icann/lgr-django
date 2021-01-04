# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from lgr_basic.views import BasicModeView

LGR_SLUG_FORMAT = r'(?P<lgr_id>[\w\_\-\.]+)'

urlpatterns = [
    url(r'^$', BasicModeView.as_view(), name='lgr_basic_mode')
]
