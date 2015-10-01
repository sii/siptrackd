from twisted.web import xmlrpc
from twisted.internet import defer

from siptrackdlib import deviceconfig

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class DeviceConfigRPC(baserpc.BaseRPC):
    node_type = 'device config'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session, parent_oid, name):
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'device config', name)
        yield self.object_store.commit(obj)
        defer.returnValue(obj.id)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_set_name(self, session, oid, name):
        node = self.getOID(session, oid)
        node.name.set(name)
        yield self.object_store.commit(node)
        defer.returnValue(True)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add_config(self, session, oid, data, timestamp):
        node = self.getOID(session, oid)
        yield node.addConfig(data, timestamp)
        defer.returnValue(True)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_get_latest_config(self, session, oid):
        node = self.getOID(session, oid)
        ret = yield node.getLatestConfig()
        if ret is None:
            ret = False
        else:
            ret = list(ret)
        defer.returnValue(ret)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_get_all_configs(self, session, oid):
        node = self.getOID(session, oid)
        ret = yield node.getAllConfigs()
        ret = list(ret)
        defer.returnValue(ret)

def device_config_data_extractor(node, user):
    return [node.name.get()]

gatherer.node_data_registry.register(deviceconfig.DeviceConfig,
        device_config_data_extractor)

