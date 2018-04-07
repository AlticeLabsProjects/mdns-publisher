#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# setup.py - Avahi/mDNS name publisher module.
#
# Copyright (c) 2018, Carlos Rodrigues
#


from setuptools import setup


manifest = {
    "name": "mdns-publisher",
    "version": "1.0",
    "description": "Publish CNAMEs pointing to the local host over Avahi/mDNS",
    "author": "Carlos Rodrigues",
    "author_email": "cefrodrigues@gmail.com",
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
}


setup(**manifest)


# vim: set expandtab ts=4 sw=4:
