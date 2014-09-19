from twisted.web import xmlrpc
from twisted.internet import defer

from siptrackdlib import event

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class CommandQueueRPC(baserpc.BaseRPC):
    node_type = 'command queue'

class CommandRPC(baserpc.BaseRPC):
    node_type = 'command'

    @defer.inlineCallbacks
    @helpers.ValidateSession()
    def xmlrpc_set_freetext(self, session, oid, value):
        """Set value."""
        node = self.getOID(session, oid)
        node._freetext.set(value)
        yield node.commit()
        defer.returnValue(value)

class EventRPC(baserpc.BaseRPC):
    pass

class EventTriggerRPC(baserpc.BaseRPC):
    node_type = 'event trigger'

class EventTriggerRuleRPC(baserpc.BaseRPC):
    pass

class EventTriggerRulePythonRPC(baserpc.BaseRPC):
    node_type = 'event trigger rule python'

    @defer.inlineCallbacks
    @helpers.ValidateSession()
    def xmlrpc_set_code(self, session, oid, value):
        """Set value."""
        node = self.getOID(session, oid)
        node._code.set(value)
        yield node.commit()
        defer.returnValue(value)

def command_queue_data_extractor(node, user):
    return []

def command_data_extractor(node, user):
    return [node._freetext.get()]

def event_trigger_data_extractor(node, user):
    return []

def event_trigger_rule_python_data_extractor(node, user):
    return [node._code.get(), node._error.get(), node._error_timestamp.get()]

gatherer.node_data_registry.register(event.CommandQueue,
        command_queue_data_extractor)
gatherer.node_data_registry.register(event.Command,
        command_data_extractor)
gatherer.node_data_registry.register(event.EventTrigger,
        event_trigger_data_extractor)
gatherer.node_data_registry.register(event.EventTriggerRulePython,
        event_trigger_rule_python_data_extractor)
