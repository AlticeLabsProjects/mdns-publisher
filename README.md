# Avahi/mDNS CNAME publisher

This service publishes CNAME records pointing to the local host over
[multicast DNS](http://www.multicastdns.org) using the [Avahi](http://www.avahi.org/wiki/AboutAvahi)
daemon found in all major Linux distributions. Useful as a poor-man's service discovery or as a
helper for named virtual-hosts in development environments.

Since Avahi is compatible with Apple's [Bonjour](https://www.apple.com/support/bonjour),
these names are usable from MacOS X and Windows too.

## Running

Pass (one or more) CNAMEs as command-line arguments to `publish-cname.py`:

```
$ ./publish-cname.py name01.local name02.local
```

Names are restricted to the `.local` domain, but can have arbitrary sub-domains of your choosing:

```
$ ./publish-cname.py name01.local name02.local name03.mysubdomain.local
```

If the server running `publish-cname.py` is being announced over mDNS as `myserver.local`, all of
these names will be answered by Avahi as CNAMEs for `myserver.local`, regardless of any sub-domains
they might have. They remain available as long as `publish-cname.py` is running.

Run `publish-cname.py` with no arguments to find out about the available options.

## Integrating

The `AvahiPublisher` class as contained in `mpublisher.py` can be integrated into your application
to have it publish its own CNAMEs.

## Dependencies

Besides a working Avahi daemon, this service requires the Python bindings for both Avahi and D-BUS
(eg. as provided by the `python-avahi` and `python-dbus` packages in Debian).
