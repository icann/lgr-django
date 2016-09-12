#!/bin/env python2
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='lgr-django',
    version='1.6',
    author='Viagenie and Wil Tan',
    author_email='support@viagenie.ca',
    packages=find_packages('src'),
    package_dir = {'':'src'},
    license='TODO',
    description='Web-application for LGR editing',
    long_description=open('README.md').read(),
    include_package_data=True,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django :: 1.8',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[
        # Core stuff
        'Django',
        'django-widget-tweaks',
        'celery',
        # LGR/Unicode modules
        'lgr-core',
        'munidata',
        'picu',
    ]
)
