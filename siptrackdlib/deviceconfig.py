"""Device configuration management.

The nodes types in this file are intended to be used to store for example
configuration dumps from switched, routers etc.
Ie. text based configuration for specific devices.

DeviceConfig will automatically handle versioning. New configuration will
only be stored if it differs from the old version etc.
"""


import time
from string import Template
from twisted.internet import defer

from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import permission
from siptrackdlib import errors
from siptrackdlib import storagevalue

class DeviceConfig(treenodes.BaseNode):
    class_id = 'DCON'
    class_name = 'device config'

    def __init__(self, oid, branch, name = None, max_versions = 0):
        super(DeviceConfig, self).__init__(oid, branch)
        self.name = storagevalue.StorageValue(self, 'name', name,
                self._nameValidator)
        self.max_versions = storagevalue.StorageNumPositive(self, 'max_versions', max_versions)

    def _created(self, user):
        super(DeviceConfig, self)._created(user)
        self.name.commit()
        self.max_versions.commit()

    def _loaded(self, data):
        super(DeviceConfig, self)._loaded()
        self.name.preload(data)
        self.max_versions.preload(data)

    def _nameValidator(self, value):
        if type(value) not in [str, unicode]:
            raise errors.SiptrackError('invalid name for ConfigValue')
        for node in self.parent.listChildren(include = ['device config']):
            if node == self:
                continue
            if node.name.get() == value:
                raise errors.SiptrackError('duplicate DeviceConfig name detected')

    @defer.inlineCallbacks
    def _pruneData(self):
        max_versions = self.max_versions.get()
        if max_versions == 0:
            defer.returnValue()
        cur_versions = yield self.object_store.storage.countDeviceConfigData(self.oid)
        if cur_versions > max_versions:
            timestamps = yield self.object_store.storage.getAllDeviceConfigData(self.oid, only_timestamps = True)
            for n in range(cur_versions - max_versions):
                yield self.object_store.storage.removeDeviceConfigData(self.oid, timestamps[n][0])

    @defer.inlineCallbacks
    def addConfig(self, data):
        res = yield self.object_store.storage.getLatestDeviceConfigData(self.oid)
        if res:
            old_data, timestamp = res
            if old_data == data:
                defer.returnValue(False)
        yield self.object_store.storage.addDeviceConfigData(self.oid, data, int(time.time()))
        yield self._pruneData()
        defer.returnValue(True)

    def getLatestConfig(self):
        return self.object_store.storage.getLatestDeviceConfigData(self.oid)

    def getAllConfigs(self):
        return self.object_store.storage.getAllDeviceConfigData(self.oid)

class DeviceConfigTemplate(treenodes.BaseNode):
    class_id = 'DCTMPL'
    class_name = 'device config template'

    def __init__(self, oid, branch, template = None):
        super(DeviceConfigTemplate, self).__init__(oid, branch)
        self.template = storagevalue.StorageValue(self, 'template', template, cache_value=False)

    def _created(self, user):
        super(DeviceConfigTemplate, self)._created(user)
        self.template.commit()

    def _loaded(self, data):
        super(DeviceConfig, self)._loaded()
        self.template.preload(data)

    def _gatherAttributes(self):
        ret = {}
        for attr in self.listChildren(include=['attribute', 'versioned attribute']):
            ret[attr.name] = attr.value
        for attr in self.parent.listChildren(include=['attribute', 'versioned attribute']):
            ret['parent.%s' % (attr.name)] = attr.value
            ret['device.%s' % (attr.name)] = attr.value

    @defer.inlineCallbacks
    def expand(self, keywords):
        tmpl = yield self.template.get()
        tmpl = Template(tmpl)
        attributes = self._gatherAttributes()
        attributes.update(keywords)
        ret = tmpl.safe_substitute(attributes)
        defer.returnValue(ret)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(DeviceConfig)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(permission.Permission)
