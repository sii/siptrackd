from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import errors
from siptrackdlib import attribute
from siptrackdlib import permission

class ContainerTree(treenodes.BaseNode):
    """Container tree, a tree for containers.

    This object type is pretty much obsolete.
    """
    class_id = 'CT'
    class_name = 'container tree'

    def __init__(self, oid, branch):
        super(ContainerTree, self).__init__(oid, branch)

class Container(treenodes.BaseNode):
    """Container for attributes.

    This object type is pretty much obsolete.
    """
    class_id = 'C'
    class_name = 'container'

    def __init__(self, oid, branch):
        super(Container, self).__init__(oid, branch)


# Add the objects in this module to the object registry.
o = object_registry.registerClass(ContainerTree)
o.registerChild(Container)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(Container)
o.registerChild(Container)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

