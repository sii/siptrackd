from twisted.web import xmlrpc
from twisted.internet import defer

from siptrackdlib import config

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class ConfigRPC(baserpc.BaseRPC):
    pass

class ConfigNetworkAutoassignRPC(baserpc.BaseRPC):
    node_type = 'config network autoassign'

    @defer.inlineCallbacks
    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid, network_tree_oid, range_start,
            range_end):
        parent = self.object_store.getOID(parent_oid, user = session.user)
        nt = self.object_store.getOID(network_tree_oid, 'network tree', user = session.user)
        obj = parent.add(session.user, 'config network autoassign', nt, range_start,
                range_end)
        self.object_store.commit(obj)
        defer.returnValue(obj.oid)

    @defer.inlineCallbacks
    @helpers.ValidateSession()
    def xmlrpc_set_values(self, session, oid, network_tree_oid, range_start,
            range_end):
        node = self.object_store.getOID(oid, 'config network autoassign', user = session.user)
        nt = self.object_store.getOID(network_tree_oid, 'network tree', user = session.user)
        node.network_tree.set(nt)
        node.range_start.set(range_start)
        node.range_end.set(range_end)
        self.object_store.commit(node)
        defer.returnValue(True)

class ConfigValueRPC(baserpc.BaseRPC):
    node_type = 'config value'

    @defer.inlineCallbacks
    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid, name, value):
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'config value', name, value)
        self.object_store.commit(obj)
        defer.returnValue(obj.id)

    @defer.inlineCallbacks
    @helpers.ValidateSession()
    def xmlrpc_set_name(self, session, oid, name):
        node = self.getOID(session, oid)
        node.name.set(name)
        self.object_store.commit(node)
        defer.returnValue(True)

    @defer.inlineCallbacks
    @helpers.ValidateSession()
    def xmlrpc_set_value(self, session, oid, value):
        node = self.getOID(session, oid)
        node.value.set(value)
        self.object_store.commit(node)
        defer.returnValue(True)

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

