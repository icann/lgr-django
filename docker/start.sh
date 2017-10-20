#!/bin/bash

redis-server --daemonize yes
/usr/bin/gunicorn --error-log /var/log/lgr/gunicorn-lgr.log -w 3 -t 300 --max-requests 100 -b unix:/run/lgr/lgr-django.sock --chdir ${HOME}/lgr-django/src lgr_web.wsgi:application &
celery --app=lgr_tools --workdir=WORKDIR_TO_REPLACE/src -D --concurrency=1 --logfile=/var/log/lgr/celery-lgr.log worker &
exec nginx -g 'daemon off;'
