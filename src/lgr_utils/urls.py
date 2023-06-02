# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import path

from lgr_utils.views import RefLgrAutocomplete, RefLgrAutocompleteWithCore

urlpatterns = [
    # autocompletion
    path('ref-lgr-autocomplete/', RefLgrAutocomplete.as_view(), name='ref-lgr-autocomplete'),
    path('ref-lgr-autocomplete-core/', RefLgrAutocompleteWithCore.as_view(), name='ref-lgr-autocomplete-with-core'),
]