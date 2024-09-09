#!/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from io import open

setup(
    name='lgr-django',
    version='6.1.2',
    author='Cofomo, Viagenie and Wil Tan',
    author_email='int-eng@cofomo.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    license='BSD',
    description='Web-application for LGR editing',
    long_description=open('README.md', encoding='utf-8').read(),
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django :: 3.1',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    install_requires=[
        # Core stuff
        'Django',
        'django-widget-tweaks',
        'django-redis-cache',
        'django-autocomplete-light',
        'django-cleanup',
        'django-celery-results',
        'django-celery-beat',
        'celery',
        'okta-jwt-verifier',
        # LGR/Unicode modules
        'lgr-core',
        'munidata',
        'picu',
        # Other
        'natsort'
    ]
)
