#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.db.utils import OperationalError

from lgr_models.models.settings import LGRSettings

lgr_settings: LGRSettings = LGRSettings()
try:
    lgr_settings: LGRSettings = LGRSettings.objects.get(pk=1)
except OperationalError:
    # the table does not exist yet
    pass
