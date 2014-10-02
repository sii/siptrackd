from twisted.web import xmlrpc
from twisted.internet import defer

from siptrackdlib import eventlog

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class EventLogTreeRPC(baserpc.BaseRPC):
    node_type = 'event log tree'

class EventLogRPC(baserpc.BaseRPC):
    node_type = 'event log'

def event_log_tree_data_extractor(node, user):
    return []

def event_log_data_extractor(node, user):
    return [node._logtext.get()]

gatherer.node_data_registry.register(eventlog.EventLogTree,
        event_log_tree_data_extractor)
gatherer.node_data_registry.register(eventlog.EventLog,
        event_log_data_extractor)
