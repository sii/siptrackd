from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import permission
from siptrackdlib import errors
from siptrackdlib import storagevalue

class OptionTree(treenodes.BaseNode):
    class_id = 'OT'
    class_name = 'option tree'

    def __init__(self, oid, branch):
        super(OptionTree, self).__init__(oid, branch)

class OptionCategory(treenodes.BaseNode):
    class_id = 'OC'
    class_name = 'option category'

    def __init__(self, oid, branch):
        super(OptionCategory, self).__init__(oid, branch)

class OptionValue(treenodes.BaseNode):
    class_id = 'OV'
    class_name = 'option value'

    def __init__(self, oid, branch, value = None):
        super(OptionValue, self).__init__(oid, branch)
        self.value = storagevalue.StorageText(self, 'value', value)

    def _created(self, user):
        super(OptionValue, self)._created(user)
        self.value.commit()

    def _loaded(self, data):
        super(OptionValue, self)._loaded()
        self.value.preload(data)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(OptionTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(OptionCategory)

o = object_registry.registerClass(OptionCategory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(OptionValue)

o = object_registry.registerClass(OptionValue)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
o.registerChild(OptionValue)
