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
import re
import signal
import functools

from getopt import getopt, GetoptError
from textwrap import TextWrapper
from time import sleep

from .mpublisher import AvahiPublisher


log = logging.getLogger("mdns-publisher")


# Default Time-to-Live for mDNS records, in seconds...
DEFAULT_DNS_TTL = 60


def print_usage():
    """Output the proper usage syntax for this program."""

    print("USAGE: %s [-t <ttl>] [-f] [-v] <hostname.local> [...]" % os.path.basename(sys.argv[0]))

    wrapper = TextWrapper(width=79, initial_indent="\t", subsequent_indent="\t")

    print("\n-t/--ttl <seconds>")
    print(wrapper.fill("Set the TTL for all published records. (Default: %ds)" % DEFAULT_DNS_TTL))

    print("\n-f/--force")
    print(wrapper.fill("Publish all CNAMEs without checking if they are already being published "
                       "elsewhere on the network. This is much faster, but generally unsafe."))

    print("\n-v/--verbose")
    print(wrapper.fill("Produce extra output for debugging purposes."))

    print("\n-d/--daemon")
    print(wrapper.fill("Run the CNAME publishing service in the background."))

    print("\n-l/--log=<filename>")
    print(wrapper.fill("Send log messages into the specified file."))


def parse_args():
    """Parse and enforce command-line arguments."""

    try:
        options, args = getopt(sys.argv[1:], "t:fvdl:h", ["ttl=", "force", "verbose",
                                                          "daemon", "log=", "help"])
    except GetoptError as e:
        print("error: %s." % e, file=sys.stderr)
        print_usage()
        sys.exit(1)

    if len(args) < 1:
        print("error: parameter(s) missing.", file=sys.stderr)
        print_usage()
        sys.exit(1)

    # Minimal checking that the CNAMEs are properly formatted...
    cname_re = re.compile(r"^[a-z0-9-]{1,63}(?:\.[a-z0-9-]{1,63})*\.local$")
    cnames = [arg.strip().lower() for arg in args]

    for cname in cnames:
        if not cname_re.match(cname):
            print("error: malformed hostname: %s" % cname, file=sys.stderr)
            print_usage()
            sys.exit(1)

    ttl = DEFAULT_DNS_TTL
    force = False
    verbose = False
    daemon = False
    logname = None

    for option, value in options:
        if option in ("-h", "--help"):
            print_usage()
            sys.exit(1)
        elif option in ("-t", "--ttl"):
            ttl = int(value)
        elif option in ("-f", "--force"):
            force = True
        elif option in ("-v", "--verbose"):
            verbose = True
        elif option in ("-d", "--daemon"):
            daemon = True
        elif option in ("-l", "--log"):
            logname = value.strip()

    return (ttl, force, verbose, daemon, logname, cnames)


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
    log.debug("Cleaning up on %s...", signame)
    publisher.__del__()

    # Avahi needs time to forget us...
    sleep(1)

    os._exit(0)


def main():
    (ttl, force, verbose, daemon, logfile, cnames) = parse_args()

    # Since an eventual log file must support external log rotation, we must do this the hard way...
    format = logging.Formatter("%(asctime)s: %(levelname)s [%(process)d]: %(message)s")
    handler = logging.handlers.WatchedFileHandler(logfile) if logfile else logging.StreamHandler(sys.stderr)
    handler.setFormatter(format)
    logging.getLogger().addHandler(handler)

    # Leaving the root logger with the default level, and setting it in our own logging hierarchy
    # instead, prevents accidental triggering of third-party logging, just like $DEITY intended...
    log.setLevel(logging.DEBUG if verbose else logging.INFO)

    # This must be done after initializing the logger, so that an eventual log file gets created in
    # the right place (the user will assume that relative paths start from the current directory)...
    if daemon:
        daemonize()

    log.info("Avahi/mDNS publisher starting...")

    if force:
        log.info("Forcing CNAME publishing without collision checks")

    # The publisher needs to be initialized in the loop, to handle disconnects...
    publisher = None

    while True:
        if not publisher or not publisher.available():
            publisher = AvahiPublisher(ttl)

            # To make sure records disappear immediately on exit, clean up properly...
            signal.signal(signal.SIGTERM, functools.partial(handle_signals, publisher))
            signal.signal(signal.SIGINT, functools.partial(handle_signals, publisher))
            signal.signal(signal.SIGQUIT, functools.partial(handle_signals, publisher))

            for cname in cnames:
                status = publisher.publish_cname(cname, force)
                if not status:
                    log.error("Failed to publish '%s'", cname)
                    continue

            if publisher.count() == len(cnames):
                log.info("All CNAMEs published")
            else:
                log.warning("%d out of %d CNAMEs published", publisher.count(), len(cnames))

        # CNAMEs will exist while this service is kept alive,
        # but we don't actually need to do anything useful...
        sleep(1)


if __name__ == "__main__":
    main()


# vim: set expandtab ts=4 sw=4:
