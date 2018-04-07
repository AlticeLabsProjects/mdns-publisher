# Avahi/mDNS CNAME publisher

This service/library publishes CNAME records pointing to the local host over
[multicast DNS](http://www.multicastdns.org) using the [Avahi](http://www.avahi.org/wiki/AboutAvahi)
daemon found in all major Linux distributions. Useful as a poor-man's service discovery or as a
helper for named virtual-hosts in development environments.

Since Avahi is compatible with Apple's [Bonjour](https://www.apple.com/support/bonjour),
these names are usable from MacOS X and Windows too.

## Running

Pass (one or more) CNAMEs as command-line arguments to `mdns-publish-cname`:

```
$ mdns-publish-cname name01.local name02.local
```

Names are restricted to the `.local` domain, but can have arbitrary sub-domains of your choosing:

```
$ mdns-publish-cname name01.local name02.local name03.mysubdomain.local
```

If the server running `publish-cname.py` is being announced over mDNS as `myserver.local`, all of
these names will be answered by Avahi as CNAMEs for `myserver.local`, regardless of any sub-domains
they might have. They remain available as long as `publish-cname.py` is running.

Run `publish-cname.py` with no arguments to find out about the available options.

## Integrating

The `AvahiPublisher` class as contained in `mpublisher` module can be integrated into your application
to have it publish its own CNAMEs.

## Dependencies

Besides a working Avahi daemon, this service requires the `dbus-python` bindings which, in turn, requires
the development packages for D-Bus and D-Bus Glib (eg. `dbus-devel` and `dbus-glib-devel` in CentOS 7).

Installing the system-provided Python bindings for Avahi is optional but recommended. As a fallback,
this package provides a copy for Linux distributions where they are not readily available (eg. CentOS 6 and 7).
