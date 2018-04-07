# -*- coding: utf-8 -*-
#
# mpublisher.py - Avahi/mDNS name publisher.
#
# Copyright (c) 2014, SAPO
#


__all__ = ["AvahiPublisher"]


import logging

import dbus

try:
    from exceptions import NameError
except ImportError:  # ...not needed on Python 3.x.
    pass


# If the system-provided library isn't available, use a bundled copy instead.
# Necessary for CentOS 6/7 where there's no available "avahi-python" package.
try:
    import avahi
except ImportError:
    from . import _avahi as avahi


log = logging.getLogger("mdns-publisher.%s" % __name__)


# From "/usr/include/avahi-common/defs.h"
AVAHI_DNS_CLASS_IN = 0x01
AVAHI_DNS_TYPE_CNAME = 0x05


class AvahiPublisher(object):
    """Publish mDNS records to Avahi, using D-BUS."""

    def __init__(self, record_ttl=60):
        """Initialize the publisher with fixed record TTL value (in seconds)."""

        self.bus = dbus.SystemBus()

        path_server_proxy = self.bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER)
        self.server = dbus.Interface(path_server_proxy, avahi.DBUS_INTERFACE_SERVER)

        self.hostname = self.server.GetHostNameFqdn()
        self.record_ttl = record_ttl
        self.published = {}

        log.debug("Avahi mDNS publisher for: %s", self.hostname)


    def __del__(self):
        """Remove all published records from mDNS."""

        try:
            for group in self.published.values():
                group.Reset()
        except dbus.exceptions.DBusException as e:  # ...don't spam on broken connection.
            if e.get_dbus_name() != "org.freedesktop.DBus.Error.ServiceUnknown":
                raise


    def _fqdn_to_rdata(self, fqdn):
        """Convert an FQDN into the mDNS data record format."""

        data = []
        for part in fqdn.encode("ascii").split(b"."):
            if part:
                data.append(chr(len(part)).encode("ascii"))
                data.append(part)

        return b"".join(data) + b"\0"


    def count(self):
        """Return the number of records currently being published."""

        return len(self.published)


    def resolve(self, name):
        """Lookup the current owner for "name", using mDNS."""

        try:
            # TODO: Find out if it's possible to manipulate (shorten) the timeout...
            response = self.server.ResolveHostName(avahi.IF_UNSPEC, avahi.PROTO_UNSPEC,
                                                   name.encode("ascii"), avahi.PROTO_UNSPEC,
                                                   dbus.UInt32(0))
            return response[2].decode("ascii")
        except (NameError, dbus.exceptions.DBusException):
            return None


    def publish_cname(self, cname, force=False):
        """Publish a CNAME record."""

        if not force:
            # Unfortunately, this takes a few seconds in the expected case...
            log.info("Checking for '%s' availability...", cname)
            current_owner = self.resolve(cname)

            if current_owner:
                if current_owner != self.hostname:
                    log.error("DNS entry '%s' is already owned by '%s'", cname, current_owner)
                    return False

                # We may have discovered ourselves, but this is not a fatal problem...
                log.warning("DNS entry '%s' is already being published by this machine", cname)

        entry_group_proxy = self.bus.get_object(avahi.DBUS_NAME, self.server.EntryGroupNew())
        group = dbus.Interface(entry_group_proxy, avahi.DBUS_INTERFACE_ENTRY_GROUP)

        group.AddRecord(avahi.IF_UNSPEC, avahi.PROTO_UNSPEC, dbus.UInt32(0), cname.encode("ascii"),
                        AVAHI_DNS_CLASS_IN, AVAHI_DNS_TYPE_CNAME, self.record_ttl,
                        self._fqdn_to_rdata(self.hostname))

        group.Commit()
        self.published[cname] = group

        return True


    def unpublish(self, name):
        """Remove a published record from mDNS."""

        self.published[name].Reset()
        del self.published[name]


    def available(self):
        """Check if the connection to Avahi is still available."""

        try:
            # This is just a dummy call to test the connection...
            self.server.GetVersionString()
        except dbus.exceptions.DBusException as e:
            if e.get_dbus_name() != "org.freedesktop.DBus.Error.ServiceUnknown":
                raise

            return False

        return True


# vim: set expandtab ts=4 sw=4:
