# -*- coding: utf-8 -*-

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

from lgr_advanced.lgr_tools.celery_app import app as celery_app
