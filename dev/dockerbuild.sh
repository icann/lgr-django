#!/bin/sh

#Build container and follow logical link in the build process
Containers="lgr-base lgr-django lgr-gunicorn lgr-celery lgr-static"
#Containers="lgr-django lgr-gunicorn lgr-celery lgr-static"

for it in $Containers
do
  #So the logical links files are followed
  tar -ch -C $it . | docker build -t $it -
done
