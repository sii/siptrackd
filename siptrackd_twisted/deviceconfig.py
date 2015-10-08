from twisted.web import xmlrpc
from twisted.internet import defer
import xmlrpclib

from siptrackdlib import deviceconfig
import siptrackdlib.errors

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class DeviceConfigRPC(baserpc.BaseRPC):
    node_type = 'device config'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session, parent_oid, name, max_versions):
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'device config', name, max_versions)
        yield self.object_store.commit(obj)
        defer.returnValue(obj.oid)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_set_name(self, session, oid, name):
        node = self.getOID(session, oid)
        node.name.set(name)
        yield self.object_store.commit(node)
        defer.returnValue(True)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_set_max_versions(self, session, oid, max_versions):
        node = self.getOID(session, oid)
        node.max_versions.set(max_versions)
        yield self.object_store.commit(node)
        defer.returnValue(True)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add_config(self, session, oid, data):
        if len(data) > 1024*1024*3:
            raise siptrackdlib.errors.SiptrackError('config data to large')
        node = self.getOID(session, oid)
        yield node.addConfig(str(data))
        defer.returnValue(True)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_get_latest_config(self, session, oid):
        node = self.getOID(session, oid)
        res = yield node.getLatestConfig()
        if res is None:
            ret = False
        else:
            data, timestamp = res
            ret = [xmlrpclib.Binary(data), timestamp]
        defer.returnValue(ret)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_get_all_configs(self, session, oid):
        node = self.getOID(session, oid)
        res = yield node.getAllConfigs()
        if res is None:
            ret = None
        else:
            ret = []
            for data, timestamp in res:
                ret.append([xmlrpclib.Binary(data), timestamp])
        defer.returnValue(ret)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_get_timestamp_config(self, session, oid, timestamp):
        node = self.getOID(session, oid)
        ret = yield node.getTimestampConfig(timestamp)
        if ret is None:
            ret = False
        else:
            ret = xmlrpclib.Binary(ret)
        defer.returnValue(ret)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_get_stats(self, session, oid):
        node = self.getOID(session, oid)
        ret = yield node.getStats()
        defer.returnValue(ret)

class DeviceConfigTemplateRPC(baserpc.BaseRPC):
    node_type = 'device config template'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session, parent_oid, template):
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'device config template', str(template))
        yield self.object_store.commit(obj)
        defer.returnValue(obj.oid)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_set_template(self, session, oid, template):
        node = self.getOID(session, oid)
        node.template.set(str(template))
        yield self.object_store.commit(node)
        defer.returnValue(True)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_get_template(self, session, oid):
        node = self.getOID(session, oid)
        ret = yield node.template.get()
        ret = xmlrpclib.Binary(ret)
        defer.returnValue(ret)

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_expand(self, session, oid, keywords):
        node = self.getOID(session, oid)
        ret = yield node.expand(keywords)
        ret = xmlrpclib.Binary(ret)
        defer.returnValue(ret)

def device_config_data_extractor(node, user):
    return [node.name.get(), node.max_versions.get()]

gatherer.node_data_registry.register(deviceconfig.DeviceConfig,
        device_config_data_extractor)
gatherer.node_data_registry.register(deviceconfig.DeviceConfigTemplate,
        gatherer.no_data_extractor)

