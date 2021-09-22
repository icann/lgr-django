# LGR-Tool local development deployment

## About

This tool will permit to recreate mostly fatefully the ICANN production
environement in local container deploy with docker-compose instead of helm.

Of course as it is not a K8S environement many ajustement had to be made to
make everything possible. There is the exaustive list of change:

- No daily manage.py cronjob for DB cleanup
- No Helm/K8S deployement (Obviously)
- Use a MariaDB container instead of a localy shared sqlite DB
- Use a Redis container instead of a Redis Sentinel Cluster

## Warning

To permit a simple local deployment for developement purpose, spoof password
have been put in plain text inside the configuration files. This is NOT a good
production pratice and therefore THIS DEPLOYEMENT SCRIPT SHOULD NEVER BE USE IN
A PRODUCTION ENVIRONEMENT. At least not without removing plain text password
before hand.

## Requirement

Everything run in docker containers and is manage with the docker-compose
script so the requirement are:

- Docker service (accesible by the user)
- docker-compose script

## Use

The deployment process is very simple and is actualy pretty easy to use.

```
#Execute the lgr container build script
./dockerbuild.sh
#This step should take around 30 minutes and 1 hour the first time.
#The subsequent build should be about a minute as docker had now a build cache

#Start all the lgr microservice
docker-compose up -d

# The startup process can take about a minute the first time

#Create SuperUser (only on the first time)
docker exec lgr-gunicorn ../manage.py createsuperuser --noinput --email=eng@viagenie.ca
```

Open a browser to http://localhost:8080 and log in with:
- email: eng@viagenie.ca
- password: 1234

## Update container code

When new code need to be push inside de container, they need to be rebuild with
the new code and the currently running container change with the new image.
```
#Rebuild container (Should be fast if docker build cache still intact)
./dockerbuild.sh

#Reload the new container
docker-compose up -d
```

## Cleanup

Once finish some step are needed to remove all trace on the host computer
```
#Stop and destroy lgr container
docker-compose down

#Remove lgr images
docker image rm lgr-base lgr-django lgr-celery lgr-gunicorn lgr-static

#Remove dependancy images
docker image rm centos:8 redis traefik mariadb

#Remove persitants volumes
docker volume rm dev_lgr-redis dev_lgr-maria dev_lgr-storage
```
