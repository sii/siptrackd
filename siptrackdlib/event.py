import time

from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import permission
from siptrackdlib import errors
from siptrackdlib import storagevalue
from siptrackdlib import log

class CommandQueue(treenodes.BaseNode):
    """A command queue.

    A queue used to store events.
    """
    class_id = 'CQ'
    class_name = 'command queue'

    def __init__(self, oid, branch):
        super(CommandQueue, self).__init__(oid, branch)

    def createCommand(self, freetext, commit = True):
        cmd = self.add(None, 'command', freetext)
        # This is not a great solution, but a necessary evil.
        # createCommand is used in scripted triggers which really shouldn't
        # need to have to deal with command returning deferreds, so this
        # is the compromise.
        if commit:
            cmd.commit()
        return cmd

class Command(treenodes.BaseNode):
    """A command queue command.
    """
    class_id = 'C'
    class_name = 'command'

    def __init__(self, oid, branch, freetext = None):
        super(Command, self).__init__(oid, branch)
        self._freetext = storagevalue.StorageText(self, 'freetext', freetext)

    def _created(self, user):
        super(Command, self)._created(user)
        self._freetext.commit()

    def _loaded(self, data = None):
        super(Command, self)._loaded(data)
        if data != None:
            self._freetext.preload(data)

class EventTrigger(treenodes.BaseNode):
    class_id = 'ET'
    class_name = 'event trigger'

    def __init__(self, oid, branch):
        super(EventTrigger, self).__init__(oid, branch)

    def _created(self, user):
        super(EventTrigger, self)._created(user)
        self.object_store.event_triggers.append(self)

    def _loaded(self, data = None):
        super(EventTrigger, self)._loaded(data)
        if data != None:
            pass

    def _remove(self, *args, **kwargs):
        super(EventTrigger, self)._remove(*args, **kwargs)
        self.object_store.event_triggers.remove(self)

    def triggerEvent(self, event_type, *event_args, **event_kwargs):
        for rule in self.listRules():
            rule.triggerEvent(event_type, self, *event_args, **event_kwargs)

    def listRules(self):
        return self.listChildren(include = ['event trigger rule python'])

    def getCommandQueue(self, name):
        ret = None
        for queue in self.object_store.view_tree.listChildren(include = ['command queue']):
            if queue.getAttributeValue('name') == name:
                ret = queue
        return ret

class EventTriggerRulePython(treenodes.BaseNode):
    class_id = 'ETRP'
    class_name = 'event trigger rule python'

    def __init__(self, oid, branch, code = None):
        super(EventTriggerRulePython, self).__init__(oid, branch)
        self._code = storagevalue.StorageText(self, 'code', code)
        self._error = storagevalue.StorageText(self, 'error')
        self._error_timestamp = storagevalue.StorageNumPositive(self, 'error_timestamp')
        self._compiled_code = None

    def _created(self, user):
        super(EventTriggerRulePython, self)._created(user)
        self._code.commit()
        self._error.set('')
        self._error_timestamp.set(0)

    def _loaded(self, data = None):
        super(EventTriggerRulePython, self)._loaded(data)
        if data != None:
            self._code.preload(data)
            self._error.preload(data)
            self._error_timestamp.preload(data)

    def triggerEvent(self, event_type, event_trigger, *event_args, **event_kwargs):
        self.run(event_type, event_trigger, *event_args, **event_kwargs)

    def run(self, event_type, event_trigger, *args, **kwargs):
        if event_type in ['node add', 'node remove', 'node update', 'node relocate']:
            node = args[0]
        elif event_type in ['node associate', 'node disassociate']:
            node1, node2 = args
        try:
            exec self._code.get()
            if self._error_timestamp.get() != 0:
                self._error_timestamp.set(0)
                self._error.set('')
        except Exception, e:
            log.msg('Exception caught when running %s: %s' % (self, str(e)))
            self._error_timestamp.set(int(time.time()))
            self._error.set(str(e))

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Command)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(CommandQueue)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(Command)

o = object_registry.registerClass(EventTriggerRulePython)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(EventTrigger)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(EventTriggerRulePython)

