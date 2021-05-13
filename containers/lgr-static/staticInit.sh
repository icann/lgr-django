#! /bin/sh

# This script is the entrypoint of the lgr-gunicorn container
# It execute the gunicorn service with the CMD argument

set -e

# Create/Update django database
su -c '../manage.py collectstatic' lgr

# Start nginx
nginx "$@"
