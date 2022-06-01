# -*- coding: utf-8 -*-

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

from lgr_web.celery_app import app
