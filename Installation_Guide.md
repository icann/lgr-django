# LGR Toolset Web Application

This application aims to be an easy-to-use editing and authoring tool for LGR.

## Conventions

In this document, commands executed as a user are prefixed with `$`, whereas
commands executed as root are prefixed with `#`. Some commands will need to be
executed in a virtualenv (see below), and will be prefixed with `(venv)$`.

This document was written for CentOS 7, 64 bits, **with SELinux disabled**.
To disable SELinux:

	# setenforce 0

and make sure that `SELINUX` is set to `disabled` in `/etc/selinux/config`.

It should however work for other Linux distributions with some minor tweaks.

## Installation

### System configuration

Install the nginx webserver used to serve as a frontend. On CentOS, you need to
enable the EPEL repository before:

	# yum install epel-release
	# yum install nginx redis

Install virtualenv, used to create the Python environment:

	# yum install python3-virtualenv

Create a new user/group that will be used to run the application, as well as the
log directory where log files will be placed:

	# mkdir /var/www
	# useradd lgr -d /var/www/lgr
	# chmod 765 /var/www/lgr
	# mkdir -p /var/log/lgr/
	# chown lgr:lgr /var/log/lgr

Copy the archives for all provided dependencies (`picu`, `munidata`, `lgr-core`
and `lgr-django`) in a specific directory, and extract web-application:

	# su -l lgr
	$ mkdir /var/www/lgr/packages
	$ cp picu-*.tar.gz munidata-*.tar.gz lgr-core-*.tar.gz lgr-django-*.tar.gz /var/www/lgr/packages
	$ mkdir /var/www/lgr/lgr-django
	$ tar xvf /var/www/lgr/packages/lgr-django-*.tar.gz -C /var/www/lgr/lgr-django --strip-components=1

Create and configure the virtualenv:

	$ virtualenv-3 /var/www/lgr/venv
	$ source /var/www/lgr/venv/bin/activate
	(venv)$ cd /var/www/lgr/lgr-django
	(venv)$ pip install -r etc/requirements.txt -f /var/www/lgr/packages

Also install the application server:

	(venv)$ pip install gunicorn

## ICU installation

If your distribution ships ICU, install it using the package manager.
Otherwise, you can [download the ICU library](http://site.icu-project.org/download/)
in various formats (source, binary packages for some distributions).
Note: You only need to install the library files (`.so.XX`) and may install other
files at your discretion.

For example, to install ICU 52 (Unicode 6.3), as root:

	# mkdir /root/icu
	# cd /root/icu
	# yum install wget
	# wget http://download.icu-project.org/files/icu4c/52.1/icu4c-52_1-RHEL6-x64.tgz
	# tar xvf icu4c-52_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.52*

The current supported ICU versions (and their corresponding Unicode version) are:

* ICU 70 (Unicode 14.0)
* ICU 67 (Unicode 13.0)
* ICU 64 (Unicode 12.0)
* ICU 62 (Unicode 11.0)
* ICU 60 (Unicode 10.0)
* ICU 58 (Unicode 9.0)
* ICU 56 (Unicode 8.0)
* ICU 54 (Unicode 7.0)
* ICU 52 (Unicode 6.3)
* ICU 50 (Unicode 6.2)
* ICU 49 (Unicode 6.1)
* ICU 46 (Unicode 6.0)
* ICU 44 (Unicode 5.2)

Once you have installed the ICU library, please make sure that the location of
the `.so` files is in the `$LD_LIBRARY_PATH` environment variable.
If not, you can adjust the configuration system-wise (if you are using the
binary packages from ICU website):

	# echo "/usr/local/lib" > /etc/ld.so.conf.d/lgr.conf
	# ldconfig

### Latest ICU versions

Starting from ICU 58 (Unicode 9.0.0), binary distributions of ICU require a newer C++ runtime that what is available on Centos7.
You will need to recompile the library in order to support the newer versions.

	# yum install gcc gcc-c++
	# mkdir icu-60 ; cd icu-60
	# wget http://download.icu-project.org/files/icu4c/60.2/icu4c-60_2-src.tgz
	# tar xvf icu4c-60_2-src.tgz
	# mkdir build ; cd build
	# # You should switch to an unpriviledged user to compile
	# ../icu/source/runConfigureICU Linux
	# make check
	# make install

## Django Configuration

A template for production configuration is provided:

	# su -l lgr
	$ source /var/www/lgr/venv/bin/activate
	(venv )$ cp /var/www/lgr/lgr-django/src/lgr_web/settings/deploy.py.template /var/www/lgr/lgr-django/src/lgr_web/settings/local.py

Please configure the `ALLOWED_HOSTS` array with the hostname serving the LGR
application. For example, if your application is available at
`lgr-editor.example.com`, then the configuration should be `ALLOWED_HOSTS = ['lgr-editor.example.com']`.
Also configure `SUPPORTED_UNICODE_VERSIONS` as well as `UNICODE_DATABASES` according to your ICU installation.

The default database, used to store sessions, users and admin LGRs, is `sqlite`.
It is possible to configure the use of another server using the `DATABASES` dictionary.

For some tools, computation is performed in background and results are sent by e-mail.
Please edit the e-mail parameters if necessary, in order to be able to send e-mails correctly, mainly
`EMAIL_HOST` that should contain the server address, `EMAIL_PORT` that should contain the server port,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` and/or `EMAIL_USE_SSL`
if your server needs such configuration and `DEFAULT_FROM_EMAIL` in order to
correctly set the e-mail sender address.

You can also set-up the broker used to pass messages between the interface
and the background task processor by using the `BROKER_URL` key.
It is also possible to set the timeout for background tasks using `CELERYD_TASK_SOFT_TIME_LIMIT`.

The `REPERTOIRE_STORAGE_LOCATION` setting can be adjusted to point to the location of
the repertoire LGR files eg. MSR. Likewise the `LGR_STORAGE_LOCATION` setting is
the location of the built-in LGR you want to provide as an example.
Finally, the `LGR_RNG_FILE` points to the RNG schema file for XML LGR files.
If you want to modify these settings, please make sure that the `lgr` user has
read-access to the new locations.

If the application is not served in HTTPS, then the two variables `SESSION_COOKIE_SECURE`
and `CSRF_COOKIE_SECURE` need to be set to `False`.

Before starting the django application for the first time, you need to run the
following commands to set the environment up:

	(venv)$ cd /var/www/lgr/lgr-django
	(venv)$ ./manage.py migrate
	(venv)$ ./manage.py collectstatic

You also have to setup a periodic clean-up of the sessions and storage. Example for a daily
run at midnight (to adapt according to your cron scheduler):

	(venv)$ crontab -e
	0 0 * * * /var/www/lgr/venv/bin/python /var/www/lgr/lgr-django/manage.py cleanstorage

You can adjust the session and storage duration with `SESSION_COOKIE_AGE` and `STORAGE_DURATION`
settings respectively. Ensure that `SESSION_COOKIE_AGE` is at least two times `STORAGE_DURATION`,
or there may be leftover directories.

If you do not want to clean storage, replace the `cleanstorage` command by `clearsessions`.

## Serving the application

To serve the application, the following architecture in used:

* The celery application is used to launch background tasks.
* The gunicorn application server is used to run the python code.
* A redis server is used to store messages between the webapp interface and the celery application and for caching.
* The nginx webserver will act as a frontend proxy as well as serving static content.
* Requests related to the application are relayed to the gunicorn server.

### Celery configurations

The celery processes will be launched by the systemd service manager.

Copy the provided service files to systemd's configuration directory:

	# cp /var/www/lgr/lgr-django/etc/systemd/lgr-celery.service /etc/systemd/system/
	# cp /var/www/lgr/lgr-django/etc/systemd/lgr-celery-beat.service /etc/systemd/system/

The processes will be automatically started with the gunicorn service so there is nothing more to do.

### Gunicorn configuration

The gunicorn process will be launched by the systemd service manager.

Copy the provided service file to systemd's configuration directory:

	# cp /var/www/lgr/lgr-django/etc/systemd/lgr-django.service /etc/systemd/system/

Also copy the temporary files configuration and create them:

	# cp /var/www/lgr/lgr-django/etc/systemd/lgr-django.conf /etc/tmpfiles.d/
	# systemd-tmpfiles --create

Reload systemd daemon and enable and enable/start the following processes:

	# systemctl daemon-reload
	# systemctl enable lgr-django
	# systemctl start lgr-django

### nginx configuration

Use the provided configuration file (in `etc/nginx/lgr-django.conf`) as a template to
configure the served host:

	# cp /var/www/lgr/lgr-django/etc/nginx/lgr-django.conf /etc/nginx/conf.d/nginx-django.conf

Edit the file and set the `server_name` value to the name of the host.

Enable nginx daemon and start it:

	# systemctl enable nginx
	# systemctl start nginx

Do not forget to configure your firewall to allow access on port 80 (or 443 if
you configure HTTPS) and output on port 25 (or any port configured for e-mail server).
