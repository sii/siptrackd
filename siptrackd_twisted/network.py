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

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, address):
        """Create a new network."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        if parent.class_name != 'network tree':
            parent = parent.getParent('network tree')
            if parent.class_name != 'network tree':
                raise siptrackdlib.errors.SiptrackError('unable to find parent network tree')
        obj = parent.addNetwork(self.user, address)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_prune(self, oid):
        """Prune a network.
        
        The network will be removed if it has no associations/references.
        """
        node = self.getOID(oid)
        return node.prune()

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_find_missing_networks(self, oid):
        """Find missing (non-existent) subnets of the given network."""
        node = self.getOID(oid)
        missing = []
        for n in node.iterMissingNetworks():
            missing.append(n.printableCIDR())
        return missing

class NetworkIPV6RPC(baserpc.BaseRPC):
    node_type = 'ipv6 network'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, address):
        """Create a new network."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        if parent.class_name != 'network tree':
            parent = parent.getParent('network tree')
            if parent.class_name != 'network tree':
                raise siptrackdlib.errors.SiptrackError('unable to find parent network tree')
        obj = parent.addNetwork(self.user, address)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_prune(self, oid):
        """Prune a network.
        
        The network will be removed if it has no associations/references.
        """
        node = self.getOID(oid)
        return node.prune()

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_find_missing_networks(self, oid):
        """Find missing (non-existent) subnets of the given network."""
        node = self.getOID(oid)
        missing = []
        for n in node.iterMissingNetworks():
            missing.append(str(n))
        return missing

class NetworkRangeIPV4RPC(baserpc.BaseRPC):
    node_type = 'ipv4 network range'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, range):
        """Create a new network range."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        if parent.class_name != 'network tree':
            parent = parent.getParent('network tree')
            if parent.class_name != 'network tree':
                raise siptrackdlib.errors.SiptrackError('unable to find parent network tree')
        obj = parent.addRange(self.user, range)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_prune(self, oid):
        """Prune a network range.
        
        The range will be removed if it has no associations/references.
        """
        node = self.getOID(oid)
        return node.prune()

class NetworkRangeIPV6RPC(baserpc.BaseRPC):
    node_type = 'ipv6 network range'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, range):
        """Create a new network range."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        if parent.class_name != 'network tree':
            parent = parent.getParent('network tree')
            if parent.class_name != 'network tree':
                raise siptrackdlib.errors.SiptrackError('unable to find parent network tree')
        obj = parent.addRange(self.user, range)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_prune(self, oid):
        """Prune a network range.
        
        The range will be removed if it has no associations/references.
        """
        node = self.getOID(oid)
        return node.prune()

class NetworkTreeRPC(baserpc.BaseRPC):
    node_type = 'network tree'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, protocol):
        """Create a new network tree."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'network tree', protocol)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_network_exists(self, oid, address):
        """Check if a network exists in a network tree.
        
        If the network exists, return its oid, otherwise False.
        """
        nt = self.getOID(oid)
        network = nt.getNetwork(address)
        if network:
            return network.oid
        return False

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_range_exists(self, oid, range):
        """Check if a network range exists in a network tree.
        
        If the network range exists, return its oid, otherwise False.
        """
        nt = self.getOID(oid)
        range = nt.getRange(range)
        if range:
            return range.oid
        return False

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_find_missing_networks(self, oid):
        """Find missing (non-existent) subnets of the network tree."""
        nt = self.getOID(oid)
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

