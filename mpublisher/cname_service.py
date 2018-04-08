#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# cname_service.py - Publish CNAMEs pointing to the local host over Avahi/mDNS.
#
# Copyright (c) 2014, SAPO
#


from __future__ import print_function


__all__ = ["main"]


import sys
import os
import logging
import logging.handlers
import syslog
import re
import signal
import functools

from argparse import ArgumentParser, ArgumentTypeError
from time import sleep

from .mpublisher import AvahiPublisher


log = logging.getLogger("mdns-publisher")


# Default Time-to-Live for mDNS records, in seconds...
DEFAULT_DNS_TTL = 60


def positive_int_arg(value):
    """Helper type (for argparse) to validate and return positive integer argument."""

    try:
        ivalue = int(value)
    except ValueError:
        raise ArgumentTypeError("invalid int value: %s" % repr(value))

    if ivalue <= 0:
        raise ArgumentTypeError("value must be greater than zero")

    return ivalue


def local_hostname_arg(hostname):
    """Helper type (for argparse) to validate and return a (normalized) local hostname argument."""

    if not re.match(r"^[a-z0-9][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)*\.local$", hostname, re.I):
        raise ArgumentTypeError("malformed CNAME: %s" % repr(hostname))

    return hostname.lower()


def parse_args():
    """Parse and enforce command-line arguments."""

    # Disable the automatic "-h/--help" argument to customize its message...
    parser = ArgumentParser(description="Publish CNAMEs pointing to the local host over Avahi/mDNS.", add_help=False)

    parser.add_argument("cnames", metavar="hostname", nargs="+", type=local_hostname_arg,
                                  help="Fully-qualified CNAME(s) to publish. Subdomains are "
                                       "allowed, but names must end with the '.local' domain.")

    parser.add_argument("-h", "--help", action="help", help="Show the available options and exit.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Produce extra output for debugging purposes.")
    parser.add_argument("-d", "--daemon", action="store_true", help="Run the publishing service in the background.")
    parser.add_argument("-f", "--force", action="store_true", help="Do not check for availability before publishing.")
    parser.add_argument("-l", "--log", metavar="log", help="Log messages into 'syslog' or the specified log file.")
    parser.add_argument("-t", "--ttl", metavar="ttl", type=positive_int_arg, default=DEFAULT_DNS_TTL,
                                       help="TTL for published records, in seconds. (Default: %d)" % DEFAULT_DNS_TTL)

    return parser.parse_args()


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
    os.umask(0o022)

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


def handle_signals(publisher, signum, frame):
    """Unpublish all mDNS records and exit cleanly."""

    signame = next(v for v, k in signal.__dict__.items() if k == signum)
    log.info("Exiting on %s...", signame)
    publisher.__del__()

    # Avahi needs time to forget us...
    sleep(1)

    os._exit(0)


def main():
    args = parse_args()

    if not args.log:
        handler = logging.StreamHandler(sys.stderr)
        format_string = "%(levelname)s: %(message)s"
    elif args.log.lower() in ("syslog", "/dev/log"):
        facility = syslog.LOG_DAEMON if args.daemon else syslog.LOG_USER
        handler = logging.handlers.SysLogHandler(address="/dev/log", facility=facility)
        format_string = os.path.basename(sys.argv[0]) + "[%(process)d]: %(levelname)s: %(message)s"
    else:
        handler = logging.handlers.WatchedFileHandler(os.path.realpath(os.path.abspath(args.log)))
        format_string = "%(asctime)s: %(levelname)s [%(process)d]: %(message)s"

    handler.setFormatter(logging.Formatter(format_string))
    logging.getLogger().addHandler(handler)

    # Leaving the root logger with the default level, and setting it in our own logging hierarchy
    # instead, prevents accidental triggering of third-party logging, just like $DEITY intended...
    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    # This must be done after initializing the logger, so that an eventual log file gets created in
    # the right place (the user will assume that relative paths start from the current directory)...
    if args.daemon:
        daemonize()

    log.info("Avahi/mDNS publisher starting...")

    if args.force:
        log.info("Forcing CNAME publishing without collision checks")

    # The publisher needs to be initialized in the loop, to handle disconnects...
    publisher = None

    while True:
        if not publisher or not publisher.available():
            if publisher:
                log.info("Lost connection with Avahi. Reconnecting...")

            publisher = AvahiPublisher(args.ttl)

            # To make sure records disappear immediately on exit, clean up properly...
            signal.signal(signal.SIGTERM, functools.partial(handle_signals, publisher))
            signal.signal(signal.SIGINT, functools.partial(handle_signals, publisher))
            signal.signal(signal.SIGQUIT, functools.partial(handle_signals, publisher))

            for cname in args.cnames:
                status = publisher.publish_cname(cname, args.force)
                if not status:
                    log.error("Failed to publish '%s'", cname)
                    continue

            if publisher.count() == len(args.cnames):
                log.info("All CNAMEs published")
            else:
                log.warning("%d out of %d CNAMEs published", publisher.count(), len(args.cnames))

        # CNAMEs will exist while this service is kept alive,
        # but we don't actually need to do anything useful...
        sleep(1)


if __name__ == "__main__":
    main()


# vim: set expandtab ts=4 sw=4:
