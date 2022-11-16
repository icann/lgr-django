#!/usr/bin/env python3
# -*- coding: utf-8 -*-


lgr_settings = None
try:
    # LGRSettings may not exist when launching migrations so we have to encapsulate in a try..except
    from lgr_models.models.settings import LGRSettings
    lgr_settings: LGRSettings = LGRSettings.objects.get(pk=1)
except:
    pass
