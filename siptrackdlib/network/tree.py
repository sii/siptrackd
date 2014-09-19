from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import template
from siptrackdlib import config
from siptrackdlib import permission
from siptrackdlib import errors
from siptrackdlib.network import ipv4
from siptrackdlib.network import ipv6

valid_protocols = ['ipv4', 'ipv6']

class NetworkTree(treenodes.BaseNode):
    class_id = 'NT'
    class_name = 'network tree'

    def __init__(self, oid, branch, protocol = None):
        super(NetworkTree, self).__init__(oid, branch)
        self._protocol = protocol

    def _created(self, user):
        super(NetworkTree, self)._created(user)
        if self._protocol not in valid_protocols:
            raise errors.SiptrackError('unknown network protocol')
        self.protocol = self._protocol

    def getFreeNetwork(self, range_start, range_end, user):
        """Find a free network somewhere between range_start and range_end

        If an available network is found it is created and returned.
        range_start and range_end can either be address strings or
        Address objects of the appropriate type.
        """
        range_start = self.addressFromString(range_start)
        range_end = self.addressFromString(range_end)
        if self.protocol == 'ipv4':
            return ipv4.get_free_network(self, range_start, range_end, user)
        elif self.protocol == 'ipv6':
            return ipv6.get_free_network(self, range_start, range_end, user)
        else:
            raise errors.SiptrackError('confused, invalid protocol in network tree?')

    def addNetwork(self, user, address):
        """Create a network appropriate for the trees protocol.
    
        Simple convenience function.
        """
        if self.protocol == 'ipv4':
            parent = ipv4.find_network_parent(self, address)
            node = parent.add(user, 'ipv4 network', address)
        elif self.protocol == 'ipv6':
            parent = ipv6.find_network_parent(self, address)
            node = parent.add(user, 'ipv6 network', address)
        else:
            raise errors.SiptrackError('confused, invalid protocol in network tree?')
        modified = [node] + node.listChildren()
        return node, modified

    def addRange(self, user, range):
        """Create a range appropriate for the trees protocol.
    
        Simple convenience function.
        """
        if self.protocol == 'ipv4':
            parent = ipv4.find_range_parent(self, range)
            return parent.add(user, 'ipv4 network range', range)
        elif self.protocol == 'ipv6':
            parent = ipv6.find_range_parent(self, range)
            return parent.add(user, 'ipv6 network range', range)
        else:
            raise errors.SiptrackError('confused, invalid protocol in network tree?')

    def networkExists(self, address):
        """Check if a network exists.

        address can be either a string or an Address object.
        """
        if self.protocol == 'ipv4':
            if ipv4.get_network(self, address):
                return True
        elif self.protocol == 'ipv6':
            if ipv6.get_network(self, address):
                return True
        else:
            raise errors.SiptrackError('confused, invalid protocol in network tree?')
        return False

    def getNetwork(self, address):
        """Return a network or None if it doesn't exist.

        address can be either a string or an Address object.
        """
        if self.protocol == 'ipv4':
            return ipv4.get_network(self, address)
        elif self.protocol == 'ipv6':
            return ipv6.get_network(self, address)
        else:
            raise errors.SiptrackError('confused, invalid protocol in network tree?')
        return False

    def getRange(self, range):
        """Return a network range or None if it doesn't exist.

        range can be either a string or a Range object.
        """
        if self.protocol == 'ipv4':
            return ipv4.get_range(self, range)
        elif self.protocol == 'ipv6':
            return ipv6.get_range(self, range)
        else:
            raise errors.SiptrackError('confused, invalid protocol in network tree?')
        return False

    def addressFromString(self, address):
        """Convert an address string to an Address object.

        If an Address object is passed in it will be returned untouched.
        """
        if self.protocol == 'ipv4':
            return ipv4.address_from_string(address)
        if self.protocol == 'ipv6':
            return ipv6.address_from_string(address)
        else:
            raise errors.SiptrackError('confused, invalid protocol in network tree?')

    def isValidAddressString(self, address):
        if self.protocol == 'ipv4':
            try:
                if ipv4.address_from_string(address):
                    return True
            except errors.SiptrackError:
                pass
        elif self.protocol == 'ipv6':
            try:
                if ipv6.address_from_string(address):
                    return True
            except errors.SiptrackError:
                pass
        return False

    def iterMissingNetworks(self):
        if self.protocol == 'ipv4':
            return ipv4.iter_missing_networks_from_tree(self)
        elif self.protocol == 'ipv6':
            return ipv6.iter_missing_networks_from_tree(self)
        else:
            raise errors.SiptrackError('confused, invalid protocol in network tree?')

    def _get_protocol(self):
        if not self._protocol:
            raise errors.MissingData('protocol has not been loaded yet')
        return self._protocol

    def _set_protocol(self, val):
        self._protocol = val
        self.storageAction('write_data', {'name': 'network-protocol', 'value': self._protocol})
    protocol = property(_get_protocol, _set_protocol)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(NetworkTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(ipv4.Network)
o.registerChild(ipv4.NetworkRange)
o.registerChild(ipv6.Network)
o.registerChild(ipv6.NetworkRange)
o.registerChild(template.NetworkTemplate)
o.registerChild(config.ConfigValue)
o.registerChild(permission.Permission)

