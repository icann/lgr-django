#! /bin/sh

# This script is the entrypoint of the lgr-gunicorn container
# It execute the gunicorn service with the CMD argument

set -e

# TODO: Fix static issue incode and remove patch
# Patch some issue with lgr migrate
mkdir -p lgr_web/storage
[ -d lgr_web/storage/resources ] || cp -r lgr_web/resources lgr_web/storage/

# Create/Update django database
../manage.py migrate

# Start gunicorn
gunicorn --capture-output "$@"
