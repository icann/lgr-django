#!/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from io import open

setup(
    name='lgr-django',
    version='3.0.0',
    author='Viagenie and Wil Tan',
    author_email='support@viagenie.ca',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    license='TODO',
    description='Web-application for LGR editing',
    long_description=open('README.md', encoding='utf-8').read(),
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django :: 1.8',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        # Core stuff
        'Django',
        'django-widget-tweaks',
        'django-redis-cache',
        'django-autocomplete-light',
        'celery',
        # LGR/Unicode modules
        'lgr-core',
        'munidata',
        'picu',
        # Other
        'natsort'
    ]
)
