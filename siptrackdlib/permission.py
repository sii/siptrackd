from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import errors
from siptrackdlib import storagevalue

class Permission(treenodes.BaseNode):
    """A tree permission node.

    Used to indicate user/group permissions for locations in the object
    tree.
    """
    class_id = 'PERM'
    class_name = 'permission'
    require_admin = True

    def __init__(self, oid, branch, read_access = None, write_access = None,
            users = None, groups = None, all_users = None, recursive = None):
        super(Permission, self).__init__(oid, branch)
        self.read_access = storagevalue.StorageBool(self,
                'read_access', read_access)
        self.write_access = storagevalue.StorageBool(self,
                'write_access', write_access)
        self.users = storagevalue.StorageNodeList(self,
                'users', users, self._validateUsers)
        self.groups = storagevalue.StorageNodeList(self,
                'groups', groups, self._validateGroups)
        self.all_users = storagevalue.StorageBool(self,
                'all_users', all_users)
        self.recursive = storagevalue.StorageBool(self,
                'recursive', recursive)

    def _created(self, user):
        super(Permission, self)._created(user)
        self.read_access.commit()
        self.write_access.commit()
        self.users.commit()
        self.groups.commit()
        self.all_users.commit()
        self.recursive.commit()
        # Clear the global permission cache when a new permission
        # is created.
        self.perm_cache.clear()

    def _loaded(self, data = None):
        super(Permission, self)._loaded(data)
        self.read_access.preload(data)
        self.write_access.preload(data)
        self.users.preload(data)
        self.groups.preload(data)
        self.all_users.preload(data)
        self.recursive.preload(data)

    def _validateUsers(self, value):
        if type(value) != list:
            raise errors.SiptrackError('invalid value for permission users')
        for node in value:
            if node.class_name not in ['user local', 'user ldap', 'user active directory']:
                raise errors.SiptrackError('invalid value for permission users')

    def _validateGroups(self, value):
        if type(value) != list:
            raise errors.SiptrackError('invalid value for permission groups')
        for node in value:
            if node.class_name not in ['user group', 'user group ldap', 'user group active directory']:
                raise errors.SiptrackError('invalid value for permission groups')

    def matchesUser(self, user):
        if self.all_users.get():
            return True
        if not user:
            return False
        for u in self.users.get():
            if user.oid == u.oid:
                return True
        for g in self.groups.get():
            for u in g.users.get():
                if user.oid == u.oid:
                    return True
        return False

    def _remove(self, *args, **kwargs):
        super(Permission, self)._remove(*args, **kwargs)
        # Clear the global permission cache when a permission
        # is removed.
        self.perm_cache.clear()

    def _relocate(self, *args, **kwargs):
        super(Permission, self)._relocate(*args, **kwargs)
        # Clear the global permission cache when a permission
        # is moved.
        self.perm_cache.clear()

# Add the objects in this module to the object registry.
o = object_registry.registerClass(Permission)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

