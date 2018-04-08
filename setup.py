#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# setup.py - Avahi/mDNS name publisher module.
#
# Copyright (c) 2018, Carlos Rodrigues
#


import os

from setuptools import setup


manifest = {
    "name": "mdns-publisher",
    "version": "0.9.2",
    "description": "Publish CNAMEs pointing to the local host over Avahi/mDNS",
    "author": "Carlos Rodrigues",
    "author_email": "cefrodrigues@gmail.com",
    "url": "https://github.com/carlosefr/mdns-publisher",
    "packages": [
        "mpublisher",
        "mpublisher._avahi"
    ],
    "install_requires": [
        "dbus-python >= 1.1",
    ],
    "scripts": [
        "mdns-publish-cname",
    ],
    "license": "MIT",
    "keywords": "Avahi mDNS CNAME",
    "long_description": open(os.path.join(os.path.dirname(__file__), "README.rst")).read(),
    "classifiers": [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
    ],
    "zip_safe": False,
}


setup(**manifest)


# vim: set expandtab ts=4 sw=4:
