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

    def __init__(self, oid, branch, logtext = None):
        super(EventLog, self).__init__(oid, branch)
        self._logtext = storagevalue.StorageText(self, 'logtext', logtext)

    def _created(self, user):
        super(EventLog, self)._created(user)
        self._logtext.commit()

    def _loaded(self, data = None):
        super(EventLog, self)._loaded(data)
        if data != None:
            self._logtext.preload(data)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(EventLogTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(EventLog)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
