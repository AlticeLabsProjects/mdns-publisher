#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# daemonize.py - Function(s) to turn a Python process into a daemon.
#
# Copyright (c) 2013, SAPO
#


# Make an eventual port to Python 3.x easier...
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import


import sys
import os


def daemonize():
    """Run the process in the background as a daemon."""

    try:
        # First fork to return control to the shell...
        pid = os.fork()
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    if pid:
        # Quickly terminate the parent process...
        os._exit(0)

    os.setsid()

    try:
        # Second fork to prevent zombies...
        pid = os.fork()
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    if pid:
        # Quickly terminate the parent process...
        os._exit(0)

    # To make sure we don't block an unmount in the future, in case
    # the current directory resides on a mounted filesystem...
    os.chdir("/")

    # Sanitize permissions...
    os.umask(022)

    # Redirect the standard file descriptors to "/dev/null"...
    f = open(os.devnull, "r")
    os.dup2(f.fileno(), sys.stdin.fileno())
    assert sys.stdin.fileno() == 0

    f = open(os.devnull, "r")
    os.dup2(f.fileno(), sys.stdout.fileno())
    assert sys.stdout.fileno() == 1

    f = open(os.devnull, "r")
    os.dup2(f.fileno(), sys.stderr.fileno())
    assert sys.stderr.fileno() == 2


# vim: set expandtab ts=4 sw=4:
