# -*- coding: utf-8 -*-

import os

from celery import Celery
from celery.signals import setup_logging

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lgr_web.settings')

app = Celery('lgr_web')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@setup_logging.connect
def celery_setup_logging(loglevel, logfile, format, colorize, **kwargs):
    import logging.config
    logging.config.dictConfigClass(settings.LOGGING).configure()
