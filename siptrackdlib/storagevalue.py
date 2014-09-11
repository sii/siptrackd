from siptrackdlib import errors

class StorageValue(object):
    """Simple wrapper for storage access for a single variable."""
    _write_none = False

    def __init__(self, node, name, value = None, validator = None):
        self.storage = node.storage
        self.node = node
        self.oid = node.oid
        self.object_store = node.branch.tree.ext_data
        self.name = name
        self.value = value
        self._has_value = False
        if value is not None:
            self._has_value = True
        self.value = value
        self._validator_cb = validator

    def _setValue(self, value):
        """Prepare value for writing to storage.

        This does nothing here, subclasses may override where necessary.
        """
        return value

    def _getValue(self, value):
        """Parse value after having read from storage.

        This does nothing here, subclasses may override where necessary.
        """
        return value

    def _validator(self, value):
        """Validate a value that is about to be written to storage (set).
        
        Calls a validator callback supplied by our creator if one exists.
        """
        if self._validator_cb:
            self._validator_cb(value)

    def set(self, value):
        """Set the value.

        Both locally and in storage.
        """
        self._validator(value)
        self._has_value = True
        self.value = value
        # Don't write anything if the Value is None.
        if self.value is None and not self._write_none:
            return
        value = self._setValue(self.value)
        self.storage.writeData(self.oid, self.name, value)
        self.node.setModified()

    def get(self):
        """Return the value.

        Load from storage if necessary.
        """
        if not self._has_value:
            self._has_value = True
            # self.value is set to None if nothing exists in storage.
            self.value = self.storage.readData(self.oid,
                    self.name)
            self.value = self._getValue(self.value)
        return self.value

    def commit(self):
        """Save the locally stored value to storage.

        Used to write the value given when instanciating the object to
        storage.
        """
        self.set(self.value)

    def preload(self, data):
        """Load existing storage data that is passed in.

        Expects data as passed in by ObjectStorage.preload.
        The data will not be saved to storage.
        """
        if data is not None and self.name in data:
            self._has_value = True
            self.value = data[self.name]
            self.value = self._getValue(self.value)

class StorageNode(StorageValue):
    _write_none = True

    def get(self):
        """Special get for storage nodes.

        Check if the value (node) is cached but has been deleted.
        If it has, return None instead of an invalid node.
        """
        value = super(StorageNode, self).get()
        if value and value.oid is None:
            value = None
        return value

    def _getValue(self, value):
        """Tries to load a node from an oid."""
        try:
            value = self.object_store.getOID(value)
        except errors.NonExistent:
            value = None
        return value

    def _setValue(self, value):
        if value is None:
            return None
        return value.oid

    def _validator(self, value):
        # Allow None for storing no storage node.
        if value is None:
            return
        if not hasattr(value, 'oid'):
            raise errors.SiptrackError('invalid value for type StorageNode')
        super(StorageNode, self)._validator(value)

class StorageText(StorageValue):
    def _validator(self, value):
        if type(value) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for type StorageText')
        super(StorageText, self)._validator(value)

class StorageNum(StorageValue):
    def _validator(self, value):
        if type(value) not in [int, long]:
            raise errors.SiptrackError('invalid value for type StorageNum')
        super(StorageNum, self)._validator(value)

class StorageNumPositive(StorageValue):
    def _validator(self, value):
        if type(value) not in [int, long]:
            raise errors.SiptrackError('invalid value for type StorageNumPositive')
        if value < 0:
            raise errors.SiptrackError('invalid value for type StorageNumPositive')
        super(StorageNumPositive, self)._validator(value)

class StorageBool(StorageValue):
    def _validator(self, value):
        if type(value) not in [bool]:
            raise errors.SiptrackError('invalid value for type StorageBool')
        super(StorageBool, self)._validator(value)

class StorageNodeList(StorageValue):
    def get(self):
        """Special get for storage node lists.

        Check if any of the cached nodes are missing (have been deleted
        while in our cache). Remove them from the list if they have.
        """
        value = super(StorageNodeList, self).get()
        missing = []
        for node in value:
            if node.oid is None:
                missing.append(node)
        if len(missing) > 0:
            for node in missing:
                value.remove(node)
            self.set(value)
        return value

    def _getValue(self, value):
        """Tries to load a node from an oid."""
        ret = []
        for oid in value:
            try:
                node = self.object_store.getOID(oid)
                ret.append(node)
            except errors.NonExistent:
                pass
        return ret

    def _setValue(self, value):
        ret = [node.oid for node in value]
        return ret

    def _validator(self, value):
        if type(value) != list:
            raise errors.SiptrackError('invalid value for type StorageNodeList')
        for node in value:
            if not hasattr(node, 'oid'):
                raise errors.SiptrackError('invalid value for type StorageNodeList')
        super(StorageNodeList, self)._validator(value)

