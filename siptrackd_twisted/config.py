from twisted.web import xmlrpc

from siptrackdlib import config

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class ConfigRPC(baserpc.BaseRPC):
    pass

class ConfigNetworkAutoassignRPC(baserpc.BaseRPC):
    node_type = 'config network autoassign'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, network_tree_oid, range_start,
            range_end):
        parent = self.object_store.getOID(parent_oid, user = self.user)
        nt = self.object_store.getOID(network_tree_oid, 'network tree', user = self.user)
        obj = parent.add(self.user, 'config network autoassign', nt, range_start,
                range_end)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_values(self, oid, network_tree_oid, range_start,
            range_end):
        node = self.object_store.getOID(oid, 'config network autoassign', user = self.user)
        nt = self.object_store.getOID(network_tree_oid, 'network tree', user = self.user)
        node.network_tree.set(nt)
        node.range_start.set(range_start)
        node.range_end.set(range_end)
        return True

class ConfigValueRPC(baserpc.BaseRPC):
    node_type = 'config value'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, name, value):
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'config value', name, value)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_name(self, oid, name):
        node = self.getOID(oid)
        node.name.set(name)
        return True

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_value(self, oid, value):
        node = self.getOID(oid)
        node.value.set(value)
        return True

def config_network_autoassign_data_extractor(node, user):
    oid = ''
    if node.network_tree.get():
        oid = node.network_tree.get().oid
    return [oid, node.range_start.get(), node.range_end.get()]

def config_value_data_extractor(node, user):
    return [node.name.get(), node.value.get()]

gatherer.node_data_registry.register(config.ConfigNetworkAutoassign,
        config_network_autoassign_data_extractor)
gatherer.node_data_registry.register(config.ConfigValue,
        config_value_data_extractor)

