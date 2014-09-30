import socket
import struct

from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import template
from siptrackdlib import config
from siptrackdlib import permission
from siptrackdlib import errors

def num_to_dotted_quad(network):
    """Convert an unsigned integer into a 'dotted quad' string.

    NUM -> '192.168.1.1'
    The number must be given in host byte order.
    """
    return socket.inet_ntoa(struct.pack('>L', network))

# This will _not_ make sure the netmask is valid.
def num_to_bitcount(netmask):
    """Count the number of bits set in a netmask number.

    The number must be given in host byte order.
    No validation is done to verify that the given value is a real
    netmask, use id_valid_netmask() for that.
    """
    bits = 0
    for n in range(32):
        if ((netmask >> n) & 1) == 1:
            bits += 1
    return bits

def dotted_quad_to_num(network):
    """Convert a 'dotted quad' string to an unsigned integer.

    '192.168.1.1' -> NUM
    The number is returned in host byte order.
    """
    try:
        return long(struct.unpack('>L',socket.inet_aton(network))[0])
    except socket.error, e:
        raise errors.SiptrackError('%s' % e)

def bitcount_to_num(netmask):
    """Return an unsigned integer with 'netmask' bits set.

    ie. convert a '/24' netmask count to an integer.
    The returned value is in host byte order.
    """
    res = 0L
    for n in range(netmask):
        res |= 1<<31 - n
    return res

def dotted_quad_cidr_to_num(network):
    """Convert the network string a.b.c.d/nn to network, netmask integers.

    Returns a tuple of the form (address-NUM, netmask-NUM) or (None, None)
    on error.
    """
    try:
        network, netmask = network.split('/')
    except ValueError:
        return (None, None)

    try:
        network = dotted_quad_to_num(network)
    except errors.SiptrackError:
        return (None, None)

    try:
        netmask = int(netmask)
    except ValueError:
        return (None, None)
    if netmask < 0 or netmask > 32:
        return (None, None)

    netmask = bitcount_to_num(netmask)
    network = network & netmask

    return (network, netmask)

class Address(object):
    def __init__(self, address, netmask, mask = True, validate = True):
        self.address = address
        self.netmask = netmask
        self._calcAddrData()

        if mask:
            self.address = self.network

        if validate:
            if not self._isValidNetmask(netmask):
                raise ValueError('invalid netmask')

    def clone(self):
        return Address(self.address, self.netmask, mask = False,
                validate = False)

    def _calcAddrData(self):
        self.network = self.address & self.netmask
        self.start = self.network
        self.broadcast = self.network + (0xffffffff - self.netmask)
        self.end = self.broadcast

    def __repr__(self):
        return '<IPV4.Address(%s, %s)>' % (self.address, self.netmask)

    def __str__(self):
        return self.printableCIDR()

    def __lt__(self, other):
        """True if the current address is a subnet of 'other'."""
        if self.start >= other.start and self.end <= other.end:
            if self.start > other.start or self.end < other.end:
                return True
        return False

    def __le__(self, other):
        """True if the current address is a subnet of, or equal to, 'other'."""
        if self.start >= other.start and self.end <= other.end:
            return True
        return False

    def __eq__(self, other):
        """True if the addresses are identical."""
        if self.start == other.start and self.end == other.end:
            return True
        return False
    
    def __ne__(self, other):
        """True if the address are not identical."""
        if self.start != other.start or self.end != other.end:
            return True
        return False
    
    def __gt__(self, other):
        """True if the current address is a supernet of 'other'."""
        if other.start >= self.start and other.end <= self.end:
            if other.start > self.start or other.end < self.end:
                return True
        return False
    
    def __ge__(self, other):
        """True if the current address is a supernet of, or equal to, 'other'."""
        if other.start >= self.start and other.end <= self.end:
            return True
        return False

    def _isValidNetmask(self, netmask):
        foundzero = False
        for n in range(32):
            pos = 31 - n
            val = (netmask >> pos) & 1
            if val == 0:
                foundzero = True
            if val == 1 and foundzero is True:
                return False
        return True

    def inc(self, step = 1):
        addr = self.clone()
        addr.address += step
        addr._calcAddrData()
        return addr

    def dec(self, step = 1):
        addr = self.clone()
        addr.address -= step
        addr._calcAddrData()
        return addr

    def isHigher(self, other):
        if self.address > other.address:
            return True
        return False

    def printableCIDR(self):
        return '%s/%s' % (self.numToDottedQuad(self.address),
                          self.numToBitcount(self.netmask))
    printable = printableCIDR
    
    def printableNonCIDR(self):
        return '%s %s' % (self.numToDottedQuad(self.address),
                          self.numToDottedQuad(self.netmask))

    def numToDottedQuad(self, network):
        """Convert an unsigned integer into a 'dotted quad' string.

        NUM -> '192.168.1.1'
        The number must be given in host byte order.
        """
        return socket.inet_ntoa(struct.pack('>L', network))

    def numToBitcount(self, netmask):
        """Count the number of bits set in a netmask number.
    
        The number must be given in host byte order.
        No validation is done to verify that the given value is a real
        netmask.
        """
        bits = 0
        for n in range(32):
            if ((netmask >> n) & 1) == 1:
                bits += 1
        return bits

class Network(treenodes.BaseNode):
    class_id = 'IP4N'
    class_name = 'ipv4 network'

    def __init__(self, oid, branch, address = None):
        """Init.

        address can be eith an address string (nn.nn.nn.nn/mm) or an
        Address object.
        """
        super(Network, self).__init__(oid, branch)
        self.address = address

    def __repr__(self):
        return '<ipv4.Network(%s:%s)>' % (self.oid, self.address)

    def __str__(self):
        return '<ipv4.Network(%s:%s)>' % (self.oid, self.address)

    def _created(self, user):
        """Perform setup for a newly created network.

        This includes several steps. Make sure we match the protocol of
        the network tree we have been created in.
        Find our real parent, since we likely have been created as a child
        of the network tree, and relocate to it.
        Find any children (subnets) of ourselves and relocate to be children
        of us.
        """
        super(Network, self)._created(user)
        network_tree = self.getParent('network tree')
        if network_tree.protocol != 'ipv4':
            raise errors.SiptrackError('network type doesn\'t match network tree protocol')

        # If we were passed a string, convert it, otherwise assume
        # it's an Address object already.
        if type(self.address) in [str, unicode]:
            self.address = self.addressFromString(self.address)
        self.storageAction('write_data', {'name': 'network', 'value': self.address.network})
        self.storageAction('write_data', {'name': 'netmask', 'value': self.address.netmask})

        # Be really sure that this network is in the correct place.
        parent = find_network_parent(network_tree, self.address)
        if parent.oid != self.parent.oid:
            raise errors.SiptrackError('invalid network location')

        # Make sure an identical network doesn't exist here.
        for network in parent.listChildren(include = ['ipv4 network']):
            if self.oid == network.oid:
                continue
            if self.address == network.address:
                raise errors.SiptrackError('network already exists')

        self._collectChildren()

    def relocate(self, new_parent, user = None):
        """Public relocate method.

        Networks can't be manually relocated, their position in the network
        tree is based on the other existing networks.
        """
        if new_parent.class_name != 'network tree':
            raise errors.SiptrackError('networks can only be relocated to network trees')

        new_parent_tree = new_parent
        new_parent = find_network_parent(new_parent, self.address)

        for network in self.traverse(include_self = True, max_depth = -1,
                                     include = [self.class_name]):
            if new_parent_tree.networkExists(network.address):
                raise errors.SiptrackError('sorry, the network %s already exists in the destination tree' % (network.address))

        super(Network, self).relocate(new_parent, user)
        self._collectChildren()

    def _collectChildren(self):
        # Find any networks and ranges here that should be children of ours.
        children = []
        include = ['ipv4 network', 'ipv4 network range']
        for child in self.parent.listChildren(include = include):
            if child.oid == self.oid:
                continue
            # Ranges of the same size as the network are also collected.
            if child.address <= self.address:
                children.append(child)
        for child in children:
            child.branch.relocate(self.branch)

    def _loaded(self, data = None):
        """Called for an existing network being loaded.

        Creates self.address from storage.
        """
        self.address = Address(data['network'], data['netmask'], False, False)

    def addressFromString(self, address):
        return address_from_string(address)

    def remove(self, recursive, user = None):
        """Remove a network.
        
        Overrides Treenode.remove because when doing a non-recursive removal,
        we still want to get rid of everything except networks.
        """
        updated = []
        if not recursive:
            for child in list(self.listChildren(exclude = ['ipv4 network'])):
                updated += child.remove(recursive = True, user = user)
        updated += super(Network, self).remove(recursive, user)
        return updated
    delete = remove

    def _remove(self, *args, **kwargs):
        oid = self.oid
        parent = self.parent
        super(Network, self)._remove(*args, **kwargs)

    def prune(self, user = None):
        """Prune a network.

        The network will be removed if it has no associations/references.
        """
        if not self.hasWritePermission(user):
            raise errors.PermissionDenied()
        if len(list(self.references)) == 0 and \
                len(list(self.associations)) == 0:
            return self.remove(recursive = False)
        return []

    def iterMissingNetworks(self):
        """Return non-existent subnets.

        Each subnet is returned as an Address object.
        The largest possible networks are returned.
        """
        children = self.listChildren(include = ['ipv4 network'])
        children = [c.address for c in children]
        return iter_missing_networks(self.address, children)

    def isHost(self):
        if self.address.netmask == 0xffffffff:
            return True
        return False

    def getFreeNetwork(self, user=None):
        """Create a host (/32) subnet which is available under us.
        
        Used by Device.autoAssign and possibly others.
        """
        tree = self.getParent('network tree')
        return get_free_network(tree, self.address.first, self.address.last, user)

    def buildSearchValues(self):
        values = super(Network, self).buildSearchValues()
        if not self.removed:
            values['name'] =  unicode(self.address)
            values['network'] = unicode(self.address)
        return values

class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def clone(self):
        return Range(self.start, self.end)

    def __repr__(self):
        return '<IPV4.Range(%s, %s)>' % (self.start, self.end)

    def __str__(self):
        return self.printable()

    def __lt__(self, other):
        """True if the current address is a subnet of 'other'."""
        if self.start >= other.start and self.end <= other.end:
            if self.start > other.start or self.end < other.end:
                return True
        return False

    def __le__(self, other):
        """True if the current address is a subnet of, or equal to, 'other'."""
        if self.start >= other.start and self.end <= other.end:
            return True
        return False

    def __eq__(self, other):
        """True if the addresses are identical."""
        if self.start == other.start and self.end == other.end:
            return True
        return False
    
    def __ne__(self, other):
        """True if the address are not identical."""
        if self.start != other.start or self.end != other.end:
            return True
        return False
    
    def __gt__(self, other):
        """True if the current address is a supernet of 'other'."""
        if other.start >= self.start and other.end <= self.end:
            if other.start > self.start or other.end < self.end:
                return True
        return False
    
    def __ge__(self, other):
        """True if the current address is a supernet of, or equal to, 'other'."""
        if other.start >= self.start and other.end <= self.end:
            return True
        return False

    def printable(self):
        return '%s %s' % (self.numToDottedQuad(self.start),
                          self.numToDottedQuad(self.end))
    
    def printableStart(self):
        return self.numToDottedQuad(self.start)
    
    def printableEnd(self):
        return self.numToDottedQuad(self.end)
    
    def numToDottedQuad(self, network):
        """Convert an unsigned integer into a 'dotted quad' string.

        NUM -> '192.168.1.1'
        The number must be given in host byte order.
        """
        return socket.inet_ntoa(struct.pack('>L', network))

class NetworkRange(treenodes.BaseNode):
    class_id = 'IP4NR'
    class_name = 'ipv4 network range'

    def __init__(self, oid, branch, range = None):
        """Init.

        address can be eith an address string (nn.nn.nn.nn mm.mm.mm.mm) or a
        Range object.
        """
        super(NetworkRange, self).__init__(oid, branch)
        self.range = range

    def __repr__(self):
        return '<ipv4.NetworkRange(%s:%s)>' % (self.oid, self.range)

    def __str__(self):
        return '<ipv4.NetworkRange(%s:%s)>' % (self.oid, self.range)

    def _created(self, user):
        """Perform setup for a newly created network.

        This includes several steps. Make sure we match the protocol of
        the network tree we have been created in.
        Find our real parent, since we likely have been created as a child
        of the network tree, and relocate to it.
        Find any children (subnets) of ourselves and relocate to be children
        of us.
        """
        super(NetworkRange, self)._created(user)
        network_tree = self.getParent('network tree')
        if network_tree.protocol != 'ipv4':
            raise errors.SiptrackError('network range type doesn\'t match network tree protocol')

        # If we were passed a string, convert it, otherwise assume
        # it's a Range object already.
        if type(self.range) in [str, unicode]:
            self.range = self.rangeFromString(self.range)
        self.storageAction('write_data', {'name': 'start', 'value': self.range.start})
        self.storageAction('write_data', {'name': 'end', 'value': self.range.end})

        # Be really sure that this range is in the correct place.
        parent = find_range_parent(network_tree, self.range)
        if parent.oid != self.parent.oid:
            raise errors.SiptrackError('invalid network location')

        # Make sure an identical range doesn't exist here.
        for range in parent.listChildren(include = ['ipv4 network range']):
            if self.oid == range.oid:
                continue
            if self.range == range.range:
                raise errors.SiptrackError('network range already exists')

    def relocate(self):
        """Public relocate method.

        Network ranges can't be manually relocated, their position in the
        networe tree is based on existing networks.
        """
        raise errors.SiptrackError('can\'t relocate network ranges')

    def _loaded(self, data = None):
        """Called for an existing network being loaded.

        Creates self.address from storage.
        """
        self.range = Range(data['start'], data['end'])
        self.address = self.range

    def prune(self, user = None):
        """Prune a network range.

        The range will be removed if it has no associations/references.
        """
        if len(list(self.references)) == 0 and \
                len(list(self.associations)) == 0:
            return self.remove(recursive = True)
        return []

    def rangeFromString(self, address):
        return range_from_string(address)

    # We keep an address so comparissons etc. to Network objects
    # don't break.
    def _get_address(self):
        return self.range

    def _set_address(self, val):
        self.range = val
    address = property(_get_address, _set_address)

    def getFreeNetwork(self, user=None):
        """Create a host (/32) subnet which is available under us.
        
        Used by Device.autoAssign and possibly others.
        """
        tree = self.getParent('network tree')
        return get_free_network(tree, self.range.start, self.range.end, user)

def get_free_network(tree, start, end, user=None):
    """Create a host (/32) subnet which is available under us.
    
    Used by Device.autoAssign and possibly others.
    """
    cur = start
    while not cur > end:
        if not tree.networkExists(cur):
            return tree.addNetwork(user, cur)
        cur = cur.inc()
    return None, None

#def get_free_network(base, start, end, user=None):
#    """Create a host (/32) subnet which is available under us.
#    
#    Used by Device.autoAssign and possibly others.
#    """
#    children = self.listChildren(include = ['ipv4 network'])
#    children = [c.address for c in children]
#    for start, end in iter_empty_ranges(self.address, children):
#        address = Address(start, 0xffffffff)
#        return base.add(user, 'ipv4 network', address)
#    return None

def network_sorter(x, y):
    """Simple network sorting function."""
    if x.address < y.address:
        return -1
    if x.address == y.address:
        return 0
    return 1

def iter_empty_ranges(base, children):
    """Returns ranges in 'base' not occupied by 'children'.
    
    'children' is a sorted list of subnets of 'base'.
    Each range is returned as a tuple of (start_address, end_address).
    """
    children.sort(cmp = network_sorter)
    start = base.start
    for child in children:
        if start < child.start:
            yield (start, child.start -1)
        start = child.end + 1
    if start <= base.end:
        yield (start, base.end)

def iter_networks_in_range(start, end):
    """Return networks that fit in the given range.

    The largest possible networks are returned.
    """
    while start <= end:
        # FIXME: there are better ways to find a valid netmask...
        for n in range(33):
            netmask = bitcount_to_num(n)
            address = Address(start, netmask, mask = True)
            if address.network >= start and address.broadcast <= end:
                break
        yield address
        start = address.broadcast + 1

def iter_missing_networks(base, children):
    """Return networks missing from children, limited by base.

    'base' is the entire network to be searched. 'children' is a list
    of networks (direct subnets of base) that already exist.
    The largest possible networks are returned (as Address objects).
    """
    for start, end in iter_empty_ranges(base, children):
        for address in iter_networks_in_range(start, end):
            yield address

def iter_missing_networks_from_tree(tree):
    """iter_missing_networks wrapper for network trees."""
    base = Address(0, 0)
    children = tree.listChildren(include = ['ipv4 network'])
    children = [c.address for c in children]
    return iter_missing_networks(base, children)

def address_from_string(address, mask = True, validate = True):
    """Return an Address object matching an address string.

    The address string must be an ipv4 address in cidr notion, ie.
    nn.nn.nn.nn/mm.

    If an Address object is passed in it is returned untouched.
    """
    if type(address) == Address:
        return address
    if '/' not in address:
        address = '%s/32' % (address)
    network, netmask = dotted_quad_cidr_to_num(address)
    if network is None or netmask is None:
        raise errors.InvalidNetworkAddress('invalid address string')
    return Address(network, netmask, mask, validate)

def range_from_string(range):
    """Return a Range object matching an range string.

    The range string must be two ipv4 address, start and end.
    End must be equal to or higher than start

    If a Range object is passed in it is returned untouched.
    """
    if type(range) == Range:
        return range
    split = range.split()
    if len(split) != 2:
        raise errors.SiptrackError('invalid range string')
    start = dotted_quad_to_num(split[0])
    end = dotted_quad_to_num(split[1])
    return Range(start, end)

def get_network(network_tree, address):
    """Return a network from the network tree.

    Both address strings and Address objects are allowed.
    Returns the network if it exists. Otherwise None.
    """
    address = address_from_string(address)
    parent = network_tree
    while True:
        prev_parent = parent
        for net in parent.listChildren(include = [Network.class_name]):
            if address == net.address:
                return net
            if address < net.address:
                parent = net
                break
        # Not getting any closer.
        if parent is prev_parent:
            return None

def get_range(network_tree, range):
    """Return a range from the network tree.

    Both range strings and Range objects are allowed.
    Returns the range if it exists. Otherwise None.
    """
    match = range_from_string(range)
    parent = network_tree
    while True:
        for range in parent.listChildren(include = [NetworkRange.class_name]):
            if range.range == match:
                return range
        prev_parent = parent
        for net in parent.listChildren(include = [Network.class_name]):
            if match <= net.address:
                parent = net
                break
        # Not getting any closer.
        if parent is prev_parent:
            return None
    
def find_network_parent(network_tree, address):
        """Find the nearest (direct) existing parent of this network.
        
        Starts from the network tree and searches through the existing
        networks until the smallest possible parent is found.
        """
        address = address_from_string(address, mask = True, validate = True)

        parent = network_tree
        while True:
            prev_parent = parent
            for net in parent.listChildren(include = [Network.class_name]):
                # Check so a network with our address doesn't already exist.
                # Unless, ofcourse, we happen to find our own network
                # (same oids), then we ignore us.
                if address < net.address:
                    parent = net
                    break
            # Found our nearest parent.
            if parent is prev_parent:
                break
        return parent

def find_range_parent(network_tree, range):
    """Find the nearest (direct) existing parent of a range.
    
    Starts from the network tree and searches through the existing
    networks until the smallest possible parent is found.
    """
    range = range_from_string(range)

    parent = network_tree
    while True:
        prev_parent = parent
        for net in parent.listChildren(include = [Network.class_name]):
            if range <= net.address:
                parent = net
                break
        # Found our nearest parent.
        if parent is prev_parent:
            break
    return parent

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Network)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(Network)
o.registerChild(NetworkRange)
o.registerChild(template.NetworkTemplate)
o.registerChild(config.ConfigValue)
o.registerChild(permission.Permission)

o = object_registry.registerClass(NetworkRange)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(config.ConfigValue)
o.registerChild(permission.Permission)

