#-*- coding:utf-8 -*-
#
# Copyright (C) 2010 - Brantley Harris <brantley.harris@gmail.com>
#
# Distributed under the MIT license, see LICENSE.txt

import os
from setuptools import setup, find_packages

setup(
    name='sovereign',
    version = 'dev',
    description = 'Next generation server management.',
    classifiers = [
        'Development Status :: 3 - Alpha',
    ],
    keywords = 'web server webserver',
    author = 'Brantley Harris',
    author_email = 'deadwisdom@gmail.com',
    url = '',
    license = 'MIT',
    packages = find_packages(exclude=['libs', 'tests']),
    ext_modules = [Extension("tradesocket", ["tradesocket/tradesocket.c"])],
    include_package_data=True,
    zip_safe = False,
    install_requires = [
        'eventlet>=0.9.7',
        'simplejson',
        'argparse',
        'pip',
        'virtualenv'
    ],
    entry_points = {
        'console_scripts': [
            'sovreign = sovereign:run',
        ],
    })