ABOUT
-----

This service/library publishes CNAME records pointing to the local host over multicast DNS using the **Avahi** daemon found in all major Linux distributions. Useful as a poor-man's service discovery or as a helper for named virtual-hosts in development environments.

Since Avahi is compatible with Apple's Bonjour, these names are usable from MacOS X and Windows too.

See also:

    * http://www.multicastdns.org
    * https://www.avahi.org
    * https://www.apple.com/support/bonjour

DEPENDENCIES
------------

Besides a running Avahi daemon, this service requires the ``dbus-python`` bindings which, in turn, requires the development packages for D-Bus and D-Bus Glib (eg. ``dbus-devel`` and ``dbus-glib-devel`` in CentOS 7).

INSTALLATION
------------

This package can be installed from source by running::

    python setup.py build
    python setup.py install

Or, you can install the latest stable release from PyPI::

    pip install mdns-publisher

**Note:** If you're using Python 2.7 and you get errors installing ``dbus-python``, you may need to upgrade your ``pip`` version::

    pip install --upgrade pip

RUNNING
-------

Pass (one or more) CNAMEs as command-line arguments to ``mdns-publish-cname``::

    mdns-publish-cname name01.local name02.local

Names must use the ``.local`` domain but can have arbitrary sub-domains::

    mdns-publish-cname name01.local name02.local name03.mysubdomain.local

If the server running ``mdns-publish-cname`` is being announced over mDNS as ``myserver.local``, all of these names will be answered by Avahi as CNAMEs for ``myserver.local``, regardless of any sub-domains they might have. They remain available as long as ``mdns-publish-cname`` is running.

Run ``mdns-publish-cname`` with no arguments to find out about the available options.

**Note:** You can find a sample ``mdns-publish-cname.service`` file for ``systemd`` in the source repository.

INTEGRATING
-----------

The ``AvahiPublisher`` class in the ``mpublisher`` module can be integrated into your application to have it publish its own CNAMEs.
