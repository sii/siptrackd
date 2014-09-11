from twisted.web import xmlrpc

from siptrackdlib import device

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import errors
from siptrackd_twisted import baserpc

class DeviceRPC(baserpc.BaseRPC):
    node_type = 'device'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid):
        """Create a new device."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        device = parent.add(self.user, 'device')
        return device.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_delete(self, oid, prune_networks = True):
        """Delete a device."""
        device = self.getOID(oid)
        device.delete(recursive = True, user = self.user,
                prune_networks = prune_networks)
        return True

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_autoassign_network(self, oid):
        """Autoassign a network to a device."""
        device = self.getOID(oid)
        network = device.autoAssignNetwork(self.user)
        return network.oid

class DeviceTreeRPC(baserpc.BaseRPC):
    node_type = 'device tree'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid):
        """Create a new device tree."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'device tree')
        return obj.oid

class DeviceCategoryRPC(baserpc.BaseRPC):
    node_type = 'device category'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid):
        """Create a new device category."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'device category')
        return obj.oid

gatherer.node_data_registry.register(device.Device,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(device.DeviceTree,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(device.DeviceCategory,
        gatherer.no_data_extractor)

