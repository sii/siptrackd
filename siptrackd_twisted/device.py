from twisted.web import xmlrpc

from siptrackdlib import device

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import errors
from siptrackd_twisted import baserpc

class DeviceRPC(baserpc.BaseRPC):
    node_type = 'device'

    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid):
        """Create a new device."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        device = parent.add(session.user, 'device')
        return device.oid

    @helpers.ValidateSession()
    def xmlrpc_delete(self, session, oid, prune_networks = True):
        """Delete a device."""
        device = self.getOID(session, oid)
        device.delete(recursive = True, user = session.user,
                prune_networks = prune_networks)
        return True

    @helpers.ValidateSession()
    def xmlrpc_autoassign_network(self, session, oid):
        """Autoassign a network to a device."""
        device = self.getOID(session, oid)
        network = device.autoAssignNetwork(session.user)
        return network.oid

class DeviceTreeRPC(baserpc.BaseRPC):
    node_type = 'device tree'

    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid):
        """Create a new device tree."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'device tree')
        return obj.oid

class DeviceCategoryRPC(baserpc.BaseRPC):
    node_type = 'device category'

    @helpers.ValidateSession()
    def xmlrpc_add(self, session, parent_oid):
        """Create a new device category."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'device category')
        return obj.oid

gatherer.node_data_registry.register(device.Device,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(device.DeviceTree,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(device.DeviceCategory,
        gatherer.no_data_extractor)

