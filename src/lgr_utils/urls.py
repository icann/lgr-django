# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path

from lgr_utils.views import RefLgrAutocomplete

urlpatterns = [
    # autocompletion
    path('ref-lgr-autocomplete/', RefLgrAutocomplete.as_view(), name='ref-lgr-autocomplete'),
]