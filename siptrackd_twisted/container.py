from twisted.web import xmlrpc
from twisted.internet import defer
import xmlrpclib

from siptrackdlib import container
from siptrackdlib import errors

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class ContainerTreeRPC(baserpc.BaseRPC):
    node_type = 'container tree'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session, parent_oid):
        """Create a new container tree."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'container tree')
        yield self.object_store.commit(obj)
        defer.returnValue(obj.oid)

class ContainerRPC(baserpc.BaseRPC):
    node_type = 'container'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session, parent_oid):
        """Create a new container."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'container')
        yield self.object_store.commit(obj)
        defer.returnValue(obj.oid)

gatherer.node_data_registry.register(container.ContainerTree,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(container.Container,
        gatherer.no_data_extractor)
