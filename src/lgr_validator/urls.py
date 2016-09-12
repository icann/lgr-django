# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url, patterns
from . import views


LGR_SLUG_FORMAT = r'(?P<lgr_id>[\w\_\-\.]+)'

urlpatterns = patterns('',
    url(r'^eval/{}/json/'.format(LGR_SLUG_FORMAT),
        views.validate_label_json,
        name='lgr_validate_json'),
    url(r'^eval/{}/csv/'.format(LGR_SLUG_FORMAT),
        views.validate_label_csv,
        name='lgr_validate_csv'),
    url(r'^eval/{}/'.format(LGR_SLUG_FORMAT),
        views.validate_label,
        name='lgr_validate'),
)
