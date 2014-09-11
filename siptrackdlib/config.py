from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import permission
from siptrackdlib import errors
from siptrackdlib import storagevalue

def iter_config(base_node, config_node_type, break_level_match):
    if type(config_node_type) in [str]:
        class_name = config_node_type
    else:
        class_name = config_node_type.class_name
    current = base_node
    match = False
    while current:
        for config_child in current.listChildren(include = [class_name]):
            match = True
            yield config_child
        if break_level_match and match:
            break
        current = current.parent

def get_config_value(base_node, name):
    for config_child in iter_config(base_node, ConfigValue,
            break_level_match = False):
        if config_child.name == name:
            return config.child
    return None

def get_config_network_autoassign(base_node):
    ret = list(iter_config(base_node, ConfigNetworkAutoassign,
            break_level_match = False))
    return ret

class ConfigNetworkAutoassign(treenodes.BaseNode):
    class_id = 'CFGNETAUTO'
    class_name = 'config network autoassign'

    def __init__(self, oid, branch, network_tree = None, 
            range_start = None, range_end = None):
        super(ConfigNetworkAutoassign, self).__init__(oid, branch)
        self.network_tree = storagevalue.StorageNode(self, 'network_tree',
                network_tree)
        self.range_start = storagevalue.StorageValue(self, 'range_start',
                range_start, self._rangeValidator)
        self.range_end = storagevalue.StorageValue(self, 'range_end',
                range_end, self._rangeValidator)

    def _created(self, user):
        super(ConfigNetworkAutoassign, self)._created(user)
        self.network_tree.commit()
        self.range_start.commit()
        self.range_end.commit()

    def _loaded(self, data):
        super(ConfigNetworkAutoassign, self)._loaded()
        self.network_tree.preload(data)
        self.range_start.preload(data)
        self.range_end.preload(data)

    def _rangeValidator(self, value):
        if type(value) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for range in ConfigNetworkAutoassign')
        if self.network_tree.get() is None:
            raise errors.SiptrackError('invalid network tree in ConfigNetworkAutoassign')
        if not self.network_tree.get().isValidAddressString(value):
            raise errors.SiptrackError('invalid value for range in ConfigNetworkAutoassign')

    def _networkTreeValidator(self, value):
        if value.class_name != 'network tree':
            raise errors.SiptrackError('invalid network tree in ConfigNetworkAutoassign')

class ConfigValue(treenodes.BaseNode):
    class_id = 'CFGVALUE'
    class_name = 'config value'

    def __init__(self, oid, branch, name = None, value = None):
        super(ConfigValue, self).__init__(oid, branch)
        self.name = storagevalue.StorageValue(self, 'name', name,
                self._nameValidator)
        self.value = storagevalue.StorageValue(self, 'value', value)

    def _created(self, user):
        super(ConfigValue, self)._created(user)
        self.name.commit()
        self.value.commit()

    def _loaded(self, data):
        super(ConfigValue, self)._loaded()
        self.name.preload(data)
        self.value.preload(data)

    def _nameValidator(self, value):
        if type(value) not in [str, unicode]:
            raise errors.SiptrackError('invalid name for ConfigValue')
        for node in self.parent.listChildren(include = ['config value']):
            if node == self:
                continue
            if node.name.get() == value:
                raise errors.SiptrackError('duplicate ConfigValue name detected')

# Add the objects in this module to the object registry.
o = object_registry.registerClass(ConfigNetworkAutoassign)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)

o = object_registry.registerClass(ConfigValue)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
