from twisted.web import xmlrpc
from twisted.internet import defer

from siptrackdlib import option

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class OptionRPC(baserpc.BaseRPC):
    pass

class OptionTreeRPC(baserpc.BaseRPC):
    node_type = 'option tree'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session, parent_oid):
        """Create a new option tree."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'option tree')
        yield self.object_store.commit(obj)
        defer.returnValue(obj.oid)

class OptionCategoryRPC(baserpc.BaseRPC):
    node_type = 'option category'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session, parent_oid):
        """Create a new option category."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'option category')
        yield self.object_store.commit(obj)
        defer.returnValue(obj.oid)

class OptionValueRPC(baserpc.BaseRPC):
    node_type = 'option value'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session, parent_oid, value):
        """Create a new option value."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'option value', value)
        yield self.object_store.commit(obj)
        defer.returnValue(obj.oid)


def option_value_data_extractor(node, user):
    return [node.value.get()]

gatherer.node_data_registry.register(option.OptionTree,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(option.OptionCategory,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(option.OptionValue,
        option_value_data_extractor)
