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
  * `lgr_renderer` contains the code and templates used to generate the static exports of the LGR (HTML only for now).
* `lgr_auth` contains the authentication part that is used by some apps,
* `lgr_basic` contains the code related to the simple LGR interface.
* `lgr_idn_table_review` contains the IDN table review tools. It is split into the following sub-modules:
  * `idn_admin` contains the IDN table and ICANN users management part,
  * `idn_icann` contains the IDN table ICANN review that launches a review on all the tables stored in IANA registry,
  * `idn_tool` contains a tool allowing reviewing IDN tables against the references LGRs managed by admin,
* `lgr_session` defines a session object that allows manipulating some session objects and accessing and displaying storage,

## Acknowledgment

This toolset was implemented by Viagenie (Audric Schiltknecht, Julien Bernard,
David Drouin, Vincent Gonzalez and Marc Blanchet) and Wil Tan on an ICANN contract.

## License

Copyright (c) 2015-2016 Internet Corporation for Assigned Names and
Numbers (“ICANN”). All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

    * Neither the name of the ICANN nor the names of its contributors
      may be used to endorse or promote products derived from this
      software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY ICANN AND CONTRIBUTORS ``AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ICANN OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.

## Setting up your environment for development

### Pre-requisites

* Operating system: Tested on Linux and Mac OS X 
* Python >=3.6
* [LibXML2](http://www.xmlsoft.org/) [MIT License] used by the lxml Python bindings
* [ICU4C](http://site.icu-project.org/) [ICU License]
* Python modules (listed in `etc/requirements.txt`, or dependencies thereof)
  * [Django](https://www.djangoproject.com/) version 1.8.x [BSD License]
  * [django-widget-tweaks](https://github.com/kmike/django-widget-tweaks) [MIT License]
  * [Celery](http://www.celeryproject.org/) [BSD License]
  * [lxml](http://lxml.de/) [BSD License]
  * [lgr-core](https://github.com/icann/lgr-core) [BSD License]
  * [picu](https://pypi.python.org/pypi/picu) [MIT/X License]
  * [munidata](https://github.com/icann/munidata) [BSD License]
  * [natsort](https://pypi.python.org/pypi/natsort) [MIT License]
  * [django-redis-cache](https://github.com/sebleier/django-redis-cache) [BSD License]
  * [django-autocomplete-light](https://github.com/yourlabs/django-autocomplete-light/) [MIT License]
  * [pycountry](https://github.com/flyingcircusio/pycountry) [L-GPL License]
  * [django-cleanup](https://github.com/un1t/django-cleanup) [MIT License]
* A [redis](https://redis.io/) server for cache and asynchronous computations

 For documentation generation:

* [Sphinx](http://www.sphinx-doc.org/en/stable/)
* [Graphviz](http://www.graphviz.org/)


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

#### Celery

Celery is used to handle asynchronous processing for long operations in background. A broker is used to transport messages. See Celery documentation on [broker configuration](http://docs.celeryproject.org/en/3.1/getting-started/brokers/).
The default broker used is the [redis broker](http://docs.celeryproject.org/en/3.1/getting-started/brokers/redis.html).

To launch celery, in a venv-enabled console:

    $ (venv) ./venv/bin/celery --app=lgr_web --workdir=./src worker --concurrency=2

### Hacking

Some notes for developers

* The `manage.py` script adds the `src` directory to the Python `sys.path`.


#### Templates

* `src/lgr_idn_table_review/templates` contains common templates for IDN review apps
* `src/lgr_idn_table_review/idn_tool/templates` contains IDN tool specific templates
* `src/lgr_idn_table_review/idn_icann/templates` contains IDN ICANN specific templates
* `src/lgr_idn_table_review/idn_admin/templates` contains IDN admin specific templates
* `src/lgr_web/templates` contains the base templates
* `src/lgr_auth/templates` contains authentication templates
* `src/lgr_basic/templates` contains simple interface (HTML output) templates
* `src/lgr_advanced/templates` contains common template for LGR advanced apps
* `src/lgr_advanced/lgr_renderer/templates` contains LGR renderers (html output) templates
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

## Deploying application to production

Please see Installation\_Guide

## Documentation

To generate the documentation, go to the `doc` directory and run the following command:

    (venv) $ make html

The generated documentation is available in `doc/_build/html/index.html`.
