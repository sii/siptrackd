from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import permission
from siptrackdlib import password
from siptrackdlib import counter
from siptrackdlib import errors
from siptrackdlib import template
from siptrackdlib import config
from siptrackdlib import storagevalue

class CITree(treenodes.BaseNode):
    class_id = 'CIT'
    class_name = 'ci tree'

    def __init__(self, oid, branch):
        super(CITree, self).__init__(oid, branch)

class CICategory(treenodes.BaseNode):
    class_id = 'CIC'
    class_name = 'ci category'
    
    def __init__(self, oid, branch):
        super(CICategory, self).__init__(oid, branch)

class ConfigurationItem(treenodes.BaseNode):
    class_id = 'CI'
    class_name = 'configuration item'

    def __init__(self, oid, branch):
        super(ConfigurationItem, self).__init__(oid, branch)

    def _created(self, user):
        super(ConfigurationItem, self)._created(user)

    def _loaded(self, data = None):
        super(ConfigurationItem, self)._loaded(data)


# Add the objects in this module to the object registry.
o = object_registry.registerClass(CITree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(ConfigurationItem)
o.registerChild(CICategory)
o.registerChild(template.CITemplate)
#o.registerChild(config.ConfigNetworkAutoassign)
#o.registerChild(config.ConfigValue)
o.registerChild(permission.Permission)

o = object_registry.registerClass(CICategory)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(ConfigurationItem)
o.registerChild(CICategory)
o.registerChild(template.CITemplate)
#o.registerChild(config.ConfigNetworkAutoassign)
#o.registerChild(config.ConfigValue)
o.registerChild(permission.Permission)

o = object_registry.registerClass(ConfigurationItem)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(password.Password)
#o.registerChild(config.ConfigValue)
o.registerChild(permission.Permission)

