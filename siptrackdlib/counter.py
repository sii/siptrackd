from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import permission
from siptrackdlib import errors
from siptrackdlib import storagevalue

class Counter(treenodes.BaseNode):
    """A basic counter node.

    A simple integer counter meant that increments in single value steps.
    """
    class_id = 'CNT'
    class_name = 'counter'

    def __init__(self, oid, branch):
        super(Counter, self).__init__(oid, branch)
        self._value = storagevalue.StorageValue(self, 'value')

    def _created(self, user):
        super(Counter, self)._created(user)
        self._value.set(0)

    def _loaded(self, data = None):
        super(Counter, self)._loaded(data)
        if data != None:
            self._value.preload(data)

    def inc(self):
        """Increment the counter by 1."""
        self._value.set(self._value.get() + 1)

    def dec(self):
        """Decrease the counter by 1."""
        self._value.set(self._value.get() - 1)

    def get(self):
        return self._value.get()

    def set(self, val):
        self._value.set(val)

class CounterLoop(treenodes.BaseNode):
    class_id = 'CNTLOOP'
    class_name = 'counter loop'

    def __init__(self, oid, branch, values = None):
        super(CounterLoop, self).__init__(oid, branch)
        self._value_pos = storagevalue.StorageValue(self, 'valu_pos', 0)
        self._values = storagevalue.StorageValue(self, 'values', values)

    def _created(self, user):
        super(CounterLoop, self)._created(user)
        if type(self._values.get()) != list or len(self._values.get()) < 1:
            raise errors.SiptrackError('invalid counter values supplied')
        self._value_pos.commit()
        self._values.commit()

    def _loaded(self, data = None):
        super(CounterLoop, self)._loaded(data)
        if data != None:
            self._values.preload(data)
            self._value_pos.preload(data)

    def inc(self):
        if (self._value_pos.get() + 1) < len(self._values.get()):
            self._value_pos.set(self._value_pos.get() + 1)
        else:
            self._value_pos.set(0)

    def dec(self):
        if self._value_pos.get() > 0:
            self._value_pos.set(self._value_pos.get() - 1)
        else:
            self._value_pos.set(len(self._values.get()) - 1)

    def get(self):
        return self._values.get()[self._value_pos.get()]

    def set(self, new_value):
        match = False
        for pos, value in enumerate(self._values.get()):
            if new_value == value:
                match = pos
                break
        if not match:
            raise errors.SiptrackError('invalid value for set')
        self._value_pos.set(pos)

    def getValues(self):
        return self._values.get()

    def setValues(self, values):
        if type(values) != list or len(values) < 1:
            raise errors.SiptrackError('invalid counter values supplied')
        self._values.set(values)
        self._value_pos.set(0)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Counter)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(CounterLoop)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
