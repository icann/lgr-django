# LGR Toolset Web Application

This repository contains the Django project and applications for working with LGRs.

* `lgr_web` is the main Django project that ties everything together. It has the settings, main url routes,
  most of the templates as well as static resources like CSS, Javascript and images.

The following modules are Django apps for clarity but may depend on each other, therefore using them
in another project would require some work:

* `lgr_advanced` contains the advanced tools to manipulate LGR. It is split into the following sub-modules:
  * `lgr_editor` contains the code related to the LGR web-editor.
  * `lgr_validator` contains the code related the label validation module.
  * `lgr_tools` contains the code related to all utilities: testing LGR and label sets, LGR comparisons, etc.
* `lgr_auth` contains the authentication part that is used by some apps.
* `lgr_basic` contains the code related to the simple LGR interface.
* `lgr_idn_table_review` contains the IDN table review tools. It is split into the following sub-modules:
  * `icann_tools` contains the IDN table ICANN review that launches a review on all the tables stored in IANA registry,
  * `idn_tool` contains a tool allowing reviewing IDN tables against the references LGRs managed by admin,
* `lgr_manage` contains the LGRs and users management part.
* `lgr_models` contains common models for other applications.
* `lgr_renderer` contains the code and templates used to generate the static exports of the LGR (HTML only for now).
* `lgr_session` defines a session object that allows manipulating some session objects and accessing and displaying storage.
* `lgr_tasks` provides asynchronous tasks management.
* `lgr_utils` provides common shared utilities for lgr apps.

## Acknowledgment

This toolset was implemented on an ICANN contract by: 
- Cofomo (formerly Viagenie)
  - Julien Bernard
  - Michel Bernier
  - Guillaume Blanchet
  - Marc Blanchet
  - David Drouin
  - Vincent Gonzalez
  - Audric Schiltknecht
  - Alexandre Taillon-Desrochers
- Wil Tan

## License

The license can be found [here](LICENSE).

## Setting up your environment for development

### Pre-requisites

* Operating system: Tested on Linux and Mac OS X 
* Python >=3.10
* [LibXML2](https://gitlab.gnome.org/GNOME/libxml2/-/wikis/home) [MIT License] used by the lxml Python bindings
* [ICU4C](https://icu.unicode.org/) [ICU License]
* [Redis](https://redis.io/) [BSD License] Server for cache and asynchronous computations

### Python Dependencies

#### Main Dependencies

The main dependencies are defined in the [requirements.in](etc/requirements.in) file.

* [Celery](https://docs.celeryq.dev/en/stable/) [BSD License]
* [Django](https://www.djangoproject.com/) [BSD License]
* [django-autocomplete-light](https://github.com/yourlabs/django-autocomplete-light/) [MIT License]
* [django-celery-beat](https://github.com/celery/django-celery-beat) [BSD License]
* [django-celery-results](https://github.com/celery/django-celery-results) [BSD License]
* [django-cleanup](https://github.com/un1t/django-cleanup) [MIT License]
* [django-redis](https://github.com/jazzband/django-redis) [BSD License]
* [django-widget-tweaks](https://github.com/kmike/django-widget-tweaks) [MIT License]
* [lgr-core](https://github.com/icann/lgr-core) [BSD License]
* [munidata](https://github.com/icann/munidata) [BSD License]
* [natsort](https://pypi.python.org/pypi/natsort) [MIT License]
* [okta-jwt-verifier](https://pypi.org/project/okta-jwt-verifier/) [Apache Software License]
* [picu](https://pypi.python.org/pypi/picu) [MIT/X License]


#### Testing Dependencies

The following dependencies are needed to run the test suite.

* [parameterized](https://github.com/wolever/parameterized) [BSD License]

#### Documentation Dependencies

The following dependencies are needed to build the documentation.

* [Graphviz](http://www.graphviz.org/) [Eclipse Public License]
* [Sphinx](https://www.sphinx-doc.org/en/master/) [BSD License]

### Dependency Maintenance

Uses [pip-tools](https://pip-tools.readthedocs.io/en/latest/) to pin the dependencies. Install it with the following
command:

      $ source venv/bin/activate
      $ (venv) pip install pip-tools

Use the following command to generate the [requirements.txt](etc/requirements.txt)
from the [requirements.in](etc/requirements.in) file:

      $ (venv) pip-compile --output-file=requirements.txt requirements.in

To update a dependency, use the following command:

      $ (venv) pip-compile --upgrade-package <dependency>


### Installing ICU4C

You need at least one version of ICU4C library installed.

#### Linux

If your distribution ships ICU, install it using the package manager.
Otherwise, you can [download the ICU library](http://site.icu-project.org/download/)
in various formats (source, binary packages for some distributions). The easiest way
to get up and running is to use the binaries.

For example, to install ICU 52 (Unicode 6.3):

    wget http://download.icu-project.org/files/icu4c/52.1/icu4c-52_1-RHEL6-x64.tgz
    tar xvf icu4c-52_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.52*


#### Mac OS X

Using [Homebrew](http://brew.sh/)

    brew install icu4c

If you wish to install a specific version, browse the 
[commit history of the formula](https://github.com/Homebrew/homebrew/commits/master/Library/Formula/icu4c.rb)
and install using raw URL of the file at the given version (commit hash).

For example, to install ICU 52.1 (Unicode 6.3):

    brew install https://github.com/Homebrew/homebrew/raw/de95d0b8/Library/Formula/icu4c.rb

The package will be installed in `/usr/local/Cellar/icu4c/`


#### Configuring the location of ICU4C Libraries

Once you have installed one or more versions of ICU4C, you need to configure the paths to them in Django.
The parameter is called `UNICODE_DATABASES` in `src/lgr_web/settings/local.py`.
If used Homebrew to install as above, the default paths for Unicode 6.3.0 might actually work.


### Virtual environment setup

We highly recommend using [virtualenv](https://virtualenv.pypa.io/) and [pip](https://pip.pypa.io/) for development.
If you don't have them, install them first before running the following commands.

On fresh check out, do the following to create a new virtualenv, install
dependencies and configure the project:

    $ ./bin/bootstrap

If the above did not return an error, the dependencies and basic configuration would have been set up. 

Before working on the project each time, activate the virtualenv: 

    $ . ./venv/bin/activate

Start the development server:

    $ (venv) python manage.py runserver


### Settings

The Django project uses a composite settings module style such that the `DJANGO_SETTINGS_MODULE` is `lgr_web.settings`.
To customize the settings, edit `src/lgr_web/settings/local.py` which overrides any value defined in `default.py`
(found in the same directory).


#### Persistence

Most uploaded LGR files are stored as session data. See Django documentation on
[configuring the session engine](https://docs.djangoproject.com/en/3.2/topics/http/sessions/).
The default setting is to use the configured database, which defaults to `sqlite`.

For example, to use files as a storage mechanism, the following can be added to `src/lgr_web/settings/local.py`:

    SESSION_ENGINE = 'django.contrib.sessions.backends.file'

Tools also produce result files which are stored on the server.

Both the session engine and result files may need a periodical cleaning. Consider calling periodically the following command to clear expired data:

    $ (venv) python manage.py cleanstorage

User accounts and files uploaded in IDN admin mode are stored in a database.
See the [official documentation](https://docs.djangoproject.com/en/3.2/ref/settings/#databases) to configure your database.

Default database is `sqlite`, to use MariaDB, install `mysqlclient`:

    $ (venv) pip install mysqlclient

And set the following settings:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'lgr',
            'USER': 'lgr',
            'PASSWORD': '1234',
            'HOST': 'localhost',
            'PORT': '',
        }
    }

In order to set up the database for the above configuration, do the following:

    $ mysql -u root -p
    MariaDB [(none)]> CREATE DATABASE lgr CHARACTER SET UTF8;
    MariaDB [(none)]> CREATE USER lgr@localhost IDENTIFIED BY '1234';
    MariaDB [(none)]> GRANT ALL PRIVILEGES ON lgr.* TO lgr@localhost;
    MariaDB [(none)]> FLUSH PRIVILEGES;



#### Celery

Celery is used to handle asynchronous processing for long operations in background. A broker is used to transport messages. See Celery documentation on [broker configuration](http://docs.celeryproject.org/en/3.1/getting-started/brokers/).
The default broker used is the [redis broker](http://docs.celeryproject.org/en/3.1/getting-started/brokers/redis.html).

To launch celery, in a venv-enabled console:

    $ (venv) ./venv/bin/celery --app=lgr_web --workdir=./src worker --concurrency=2

##### Periodic tasks

Celery beat is used to trigger Celery periodic tasks. The task schedule is configured in the project settings:

    CELERYBEAT_SCHEDULE = {
        "calculate_index_variant_labels_tlds": {
            "task": "lgr_tasks.tasks.calculate_index_variant_labels_tlds",
            "schedule": 3600 * 24,
        }
    }
    CELERYBEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

The beat scheduler can be launched, in a venv-enabled console:

    $ (venv) ./venv/bin/celery --app=lgr_web --workdir=./src beat


### Hacking

Some notes for developers

* The `manage.py` script adds the `src` directory to the Python `sys.path`.


#### Templates

* `src/lgr_icann/templates` contains ICANN staff tools specific templates
* `src/lgr_idn_table/templates` contains common templates for IDN review apps and IDN tool specific templates
* `src/lgr_manage/templates` contains admin tools specific templates
* `src/lgr_web/templates` contains the base templates
* `src/lgr_auth/templates` contains authentication templates
* `src/lgr_basic/templates` contains simple interface templates
* `src/lgr_renderer/templates` contains LGR renderers (HTML output) templates
* `src/lgr_tasks/templates` contains tasks monitoring templates
* `src/lgr_advanced/templates` contains common template for LGR advanced apps
* `src/lgr_advanced/lgr_validator/templates` contains LGR validator specific templates
* `src/lgr_advanced/lgr_tools/templates` contains LGR tools specific templates
* `src/lgr_advanced/lgr_editor/templates` contains LGR editor specific templates


#### Static Assets (CSS, Javascript, Images)

The static assets are stored in the following directories, using conventions supported by Django 
[static files](https://docs.djangoproject.com/en/3.1/howto/static-files/) mechanism.

* `src/lgr_web/assets`
* `src/lgr_advanced/lgr_editor/static`


#### How ICU4C is used

ICU4C is used to provide Unicode database such as character names, age and other properties.

The `UNICODE_DATABASES` setting variable tells munidata how to instantiate the implementation 
of each Unicode version that we support.

Keys are the Unicode version, like '6.3.0' Values are a dict of the kwargs to pass to the `munidata.manager.register`
function along with the version.

## Create admin

Django comes with a management tool that we can use to create users with admin role.

    $ (venv) ./manage.py createsuperuser --email=test@lgr.example

## Deploying application to production

Please see Installation\_Guide

## Documentation

To generate the documentation, go to the `doc` directory and run the following command:

    $ (venv) make html

The generated documentation is available in `doc/_build/html/index.html`.


## Translations

To generate and update translation for locales (1 and 2) run the following commands:

    ./manage.py makemessages -l <locale1> -l <locale2> -i venv
    ./manage.py compilemessages -l <locale1> -l <locale2> -i venv
