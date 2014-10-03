import time

from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import permission
from siptrackdlib import errors
from siptrackdlib import storagevalue
from siptrackdlib import log

class EventLogTree(treenodes.BaseNode):
    """An event log tree.

    Stores event logs.
    """
    class_id = 'ELT'
    class_name = 'event log tree'

    def __init__(self, oid, branch):
        super(EventLogTree, self).__init__(oid, branch)

class EventLog(treenodes.BaseNode):
    """A command queue command.
    """
    class_id = 'EL'
    class_name = 'event log'

    def __init__(self, oid, branch, event_type = None, event_data = None):
        super(EventLog, self).__init__(oid, branch)
        self._event_type = storagevalue.StorageText(self, 'event_type', event_type)
        self._event_data = storagevalue.StorageValue(self, 'event_data', event_data)

    def _created(self, user):
        super(EventLog, self)._created(user)
        self._event_type.commit()
        self._event_data.commit()

    def _loaded(self, data = None):
        super(EventLog, self)._loaded(data)
        if data != None:
            self._event_type.preload(data)
            self._event_data.preload(data)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(EventLogTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(EventLog)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
