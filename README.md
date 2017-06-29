# LGR Toolset Web Application

This repository contains the Django project and applications for working with LGRs.

* `lgr_web` is the main Django project that ties everything together. It has the settings, main url routes,
  most of the templates as well as static resources like CSS, Javascript and images.

The following modules are reusable Django apps that can be included in other Django projects.

* `lgr_editor` contains the code related to the LGR web-editor.
* `lgr_validator` contains the code related the label validation module.
* `lgr_tools` contains the code related to all utilities: testing LGR and
  label sets, LGR comparisons, etc.

## Acknowledgment

This toolset was implemented by Viagenie (Audric Schiltknecht, David
Drouin and Marc Blanchet) and Wil Tan on an ICANN contract.

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
* Python 2.7
* [LibXML2](http://www.xmlsoft.org/) [MIT License] used by the lxml Python bindings
* [ICU4C](http://site.icu-project.org/) [ICU License]
* Python modules (listed in `etc/requirements.txt`, or dependencies thereof)
  * [Django](https://www.djangoproject.com/) version 1.8.x [BSD License]
  * [django-widget-tweaks](https://github.com/kmike/django-widget-tweaks) [MIT License]
  * [Celery](http://www.celeryproject.org/) [BSD License]
  * [lxml](http://lxml.de/) [BSD License]
  * lgr-core [TBD]
  * [picu](https://pypi.python.org/pypi/picu) [MIT/X License]
  * munidata [TBD]
  * [natsort](https://pypi.python.org/pypi/natsort) [MIT License]

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

LGR files are stored as session data. See Django documentation on 
[configuring the session engine](https://docs.djangoproject.com/en/1.8/topics/http/sessions/).
The default setting is to use the configured database, which defaults to `sqlite`.

For example, to use files as a storage mechanism, the following can be added to `src/lgr_web/settings/local.py`:

    SESSION_ENGINE = 'django.contrib.sessions.backends.file'

Tools also produce result files which are stored on the server.

Both the session engine and result files may need a periodical cleaning. Consider calling periodically the following command to clear expired data:

    $ (venv) python manage.py cleanstorage


#### Celery

Celery is used to handle asynchronous processing for long operations in background. A broker is used to transport messages. See Celery documentation on [broker configuration](http://docs.celeryproject.org/en/latest/getting-started/brokers/).
The default broker used is the (experimental) [Django Database broker](http://docs.celeryproject.org/en/latest/getting-started/brokers/django.html).

To launch celery, in a venv-enabled console:

    $ (venv) ./venv/bin/celery --app=lgr_tools --workdir=./src --concurrency=2 worker

### Hacking

Some notes for developers

* The `manage.py` script adds the `src` directory to the Python `sys.path`.


#### Templates

* `src/lgr_web/templates` contains the base templates
* `src/lgr_editor/templates` contains editor-specific templates
* `src/lgr_validator/templates` contains validator-specific templates
* `src/lgr_tools/templates` contains tool-specific templates


#### Static Assets (CSS, Javascript, Images)

The static assets are stored in the following directories, using conventions supported by Django 
[staticfiles](https://docs.djangoproject.com/en/1.8/howto/static-files/) mechanism.

* `src/lgr_web/assets`
* `src/lgr_editor/static`


#### How ICU4C is used

ICU4C is used to provide Unicode database such as character names, age and other properties.

The `UNICODE_DATABASES` setting variable tells munidata how to instantiate the implementation 
of each Unicode version that we support.

Keys are the Unicode version, like '6.3.0' Values are a dict of the kwargs to pass to the `munidata.manager.register`
function along with the version.

## Deploying application on a Docker image

### Pre-requisites

* Install Docker (version 1.9).
* Copy the tarball archives of the project (lgr-core, lgr-django, munidata, picu) in the docker folder.

### Create the Docker image

The Docker image name and tag are set with the -t option name:tag.
Tag is optional (default: latest).

Build arguments are specific options for our Docker image.
At the moment you can configure the allowed hosts for Django with the hosts argument and some e-mail parameters (server address and sender).

    # cd docker
    # docker build -t lgr-toolset --build-arg hosts="lgr.example" --build-arg email_srv="email-srv.lgr.example" --build-arg email_from="webmaster@lgr.example" .

### Run the Docker image

The Docker image name and tag should be the same as in build command to run the
relevant container.

The -h option should contain an allowed host specified in the hosts argument
when building the container.

    # docker run -h lgr.example -d -p 80:80 lgr-toolset 

### Debug the Docker image

The following command allows to get a bash shell in the Docker image in order to perform debug operations:

    # docker run -h lgr.example -p 80:80 -i -t lgr-toolset bash

Then to launch the server in the Docker image run:

    # ./start.sh &

You can now debug the Docker image.


## Deploying application to production

Please see Installation\_Guide

## Documentation

To generate the documentation, go to the `doc` directory and run the following command:

    (venv) $ make html

The generated documentation is available in `doc/_build/html/index.html`.
