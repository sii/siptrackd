from twisted.web import xmlrpc

from siptrackdlib import counter

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class CounterRPC(baserpc.BaseRPC):
    node_type = 'counter'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid):
        """Create a new counter."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'counter')
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set(self, oid, value):
        """Set a counters value."""
        counter = self.getOID(oid)
        counter.set(value)
        return value

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_get(self, oid):
        """Get a counters value."""
        counter = self.getOID(oid)
        return counter.get()

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_inc(self, oid):
        """Increase a counters value."""
        counter = self.getOID(oid)
        counter.inc()
        return counter.get()

class CounterLoopRPC(baserpc.BaseRPC):
    node_type = 'counter loop'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, values):
        """Create a new counter."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'counter loop', values)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set(self, oid, value):
        """Set a counters value."""
        counter = self.getOID(oid)
        counter.set(value)
        return value

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_get(self, oid):
        """Get a counters value."""
        counter = self.getOID(oid)
        return counter.get()

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_inc(self, oid):
        """Increase a counters value."""
        counter = self.getOID(oid)
        counter.inc()
        return counter.get()

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_values(self, oid, values):
        """Set a looping counters values."""
        counter = self.getOID(oid)
        counter.setValues(values)
        return True

def counter_data_extractor(node, user):
    return [node.get()]

def counter_loop_data_extractor(node, user):
    return [node.get(), node.getValues()]

gatherer.node_data_registry.register(counter.Counter,
        counter_data_extractor)
gatherer.node_data_registry.register(counter.CounterLoop,
        counter_loop_data_extractor)

