# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url
from . import views


LGR_SLUG_FORMAT_WITH_OPT_SET = r'(?:(?P<lgr_set_id>[\w\_\-\.]+)/)?(?P<lgr_id>[\w\_\-\.]+)'

urlpatterns = [
    url(r'^{}'.format(LGR_SLUG_FORMAT_WITH_OPT_SET),
        views.LGRRendererView.as_view(),
        name='lgr_render'),
]
