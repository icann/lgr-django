#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lgr_models.models.settings import LGRSettings

lgr_settings: LGRSettings = LGRSettings.objects.get(pk=1)
