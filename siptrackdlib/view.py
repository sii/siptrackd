from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import container
from siptrackdlib import attribute
from siptrackdlib import permission
from siptrackdlib import counter
from siptrackdlib import device
from siptrackdlib import network
from siptrackdlib import password
from siptrackdlib import user
from siptrackdlib import config
from siptrackdlib import event
from siptrackdlib import storagevalue
from siptrackdlib import errors

class ViewTree(treenodes.BaseNode):
    """A view tree, contains a list of view.

    There is generally only one viewtree (oid 0).
    """
    class_id = 'VT'
    class_name = 'view tree'

    def __init__(self, oid, branch):
        super(ViewTree, self).__init__(oid, branch)
        self._user_manager = storagevalue.StorageNode(self, 'user_manager')

    def _initUserManager(self):
        """Create a new user manager if no user manager is currently set.
        
        This can happen if the view tree is newly created, or if someone
        has removed the existing active user manager, which would be dumb,
        and bad.
        Also creates a default admin user account with password admin.
        """
        if self._user_manager.get() is None:
            user_manager = self.add(None, 'user manager local')
            user_manager.add(None, 'attribute', 'name', 'text', 'default user manager')
            self._user_manager.set(user_manager)
            user_manager.add(None, 'user local', username = 'admin',
                    password = 'admin', administrator = True)

    def setActiveUserManager(self, user_manager):
        if type(user_manager) not in [user.UserManagerLocal, user.UserManagerLDAP, user.UserManagerActiveDirectory]:
            raise errors.SiptrackError('not a valid user manager')
        self._user_manager.set(user_manager)

    def _get_user_manager(self):
        return self._user_manager.get()

    def _set_user_manager(self, val):
        self.setActiveUserManager(val)
    user_manager = property(_get_user_manager, _set_user_manager)

class View(treenodes.BaseNode):
    """A network/device/everything view.

    A view is the main toplevel object type. It contains everything from
    networks to devices to counters etc.
    """
    class_id = 'V'
    class_name = 'view'

    def __init__(self, oid, branch):
        super(View, self).__init__(oid, branch)


# Add the objects in this module to the object registry.
o = object_registry.registerClass(ViewTree)
o.registerChild(View)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(user.UserManagerLocal)
if user._have_ldap:
    o.registerChild(user.UserManagerLDAP)
    o.registerChild(user.UserManagerActiveDirectory)
o.registerChild(config.ConfigValue)
o.registerChild(permission.Permission)
o.registerChild(event.CommandQueue)
o.registerChild(event.EventTrigger)

o = object_registry.registerClass(View)
o.registerChild(container.ContainerTree)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(network.NetworkTree)
o.registerChild(counter.Counter)
o.registerChild(counter.CounterLoop)
o.registerChild(device.DeviceTree)
o.registerChild(password.PasswordKey)
o.registerChild(password.PasswordTree)
o.registerChild(config.ConfigNetworkAutoassign)
o.registerChild(config.ConfigValue)
o.registerChild(permission.Permission)
