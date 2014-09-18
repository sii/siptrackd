from twisted.web import xmlrpc

from siptrackdlib import network
import siptrackdlib.errors

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class NetworkRPC(baserpc.BaseRPC):
    pass

class NetworkRangeRPC(baserpc.BaseRPC):
    pass

class NetworkIPV4RPC(baserpc.BaseRPC):
    node_type = 'ipv4 network'

    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid, address):
        """Create a new network."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        if parent.class_name != 'network tree':
            parent = parent.getParent('network tree')
            if parent.class_name != 'network tree':
                raise siptrackdlib.errors.SiptrackError('unable to find parent network tree')
        obj = parent.addNetwork(session.user, address)
        return obj.oid

    @helpers.ValidateSession()
    def xmlrpc_prune(self, session, oid):
        """Prune a network.
        
        The network will be removed if it has no associations/references.
        """
        node = self.getOID(session, oid)
        return node.prune()

    @helpers.ValidateSession()
    def xmlrpc_find_missing_networks(self, session, oid):
        """Find missing (non-existent) subnets of the given network."""
        node = self.getOID(session, oid)
        missing = []
        for n in node.iterMissingNetworks():
            missing.append(n.printableCIDR())
        return missing

class NetworkIPV6RPC(baserpc.BaseRPC):
    node_type = 'ipv6 network'

    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid, address):
        """Create a new network."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        if parent.class_name != 'network tree':
            parent = parent.getParent('network tree')
            if parent.class_name != 'network tree':
                raise siptrackdlib.errors.SiptrackError('unable to find parent network tree')
        obj = parent.addNetwork(session.user, address)
        return obj.oid

    @helpers.ValidateSession()
    def xmlrpc_prune(self, session, oid):
        """Prune a network.
        
        The network will be removed if it has no associations/references.
        """
        node = self.getOID(session, oid)
        return node.prune()

    @helpers.ValidateSession()
    def xmlrpc_find_missing_networks(self, session, oid):
        """Find missing (non-existent) subnets of the given network."""
        node = self.getOID(session, oid)
        missing = []
        for n in node.iterMissingNetworks():
            missing.append(str(n))
        return missing

class NetworkRangeIPV4RPC(baserpc.BaseRPC):
    node_type = 'ipv4 network range'

    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid, range):
        """Create a new network range."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        if parent.class_name != 'network tree':
            parent = parent.getParent('network tree')
            if parent.class_name != 'network tree':
                raise siptrackdlib.errors.SiptrackError('unable to find parent network tree')
        obj = parent.addRange(session.user, range)
        return obj.oid

    @helpers.ValidateSession()
    def xmlrpc_prune(self, session, oid):
        """Prune a network range.
        
        The range will be removed if it has no associations/references.
        """
        node = self.getOID(session, oid)
        return node.prune()

class NetworkRangeIPV6RPC(baserpc.BaseRPC):
    node_type = 'ipv6 network range'

    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid, range):
        """Create a new network range."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        if parent.class_name != 'network tree':
            parent = parent.getParent('network tree')
            if parent.class_name != 'network tree':
                raise siptrackdlib.errors.SiptrackError('unable to find parent network tree')
        obj = parent.addRange(session.user, range)
        return obj.oid

    @helpers.ValidateSession()
    def xmlrpc_prune(self, session, oid):
        """Prune a network range.
        
        The range will be removed if it has no associations/references.
        """
        node = self.getOID(session, oid)
        return node.prune()

class NetworkTreeRPC(baserpc.BaseRPC):
    node_type = 'network tree'

    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid, protocol):
        """Create a new network tree."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'network tree', protocol)
        return obj.oid

    @helpers.ValidateSession()
    def xmlrpc_network_exists(self, session, oid, address):
        """Check if a network exists in a network tree.
        
        If the network exists, return its oid, otherwise False.
        """
        nt = self.getOID(session, oid)
        network = nt.getNetwork(address)
        if network:
            return network.oid
        return False

    @helpers.ValidateSession()
    def xmlrpc_range_exists(self, session, oid, range):
        """Check if a network range exists in a network tree.
        
        If the network range exists, return its oid, otherwise False.
        """
        nt = self.getOID(session, oid)
        range = nt.getRange(range)
        if range:
            return range.oid
        return False

    @helpers.ValidateSession()
    def xmlrpc_find_missing_networks(self, session, oid):
        """Find missing (non-existent) subnets of the network tree."""
        nt = self.getOID(session, oid)
        missing = []
        for n in nt.iterMissingNetworks():
            missing.append(str(n))
        return missing

def ipv4_network_extractor(node, user):
    return [node.address.printableCIDR()]

def ipv4_network_range_extractor(node, user):
    return [node.range.printable()]

def ipv6_network_extractor(node, user):
    return [str(node.address)]

def ipv6_network_range_extractor(node, user):
    return [node.range.printable()]

def network_tree_extractor(node, user):
    return [node.protocol]

gatherer.node_data_registry.register(network.tree.NetworkTree,
        network_tree_extractor)
gatherer.node_data_registry.register(network.ipv4.Network,
        ipv4_network_extractor)
gatherer.node_data_registry.register(network.ipv4.NetworkRange,
        ipv4_network_range_extractor)
gatherer.node_data_registry.register(network.ipv6.Network,
        ipv6_network_extractor)
gatherer.node_data_registry.register(network.ipv6.NetworkRange,
        ipv6_network_range_extractor)

