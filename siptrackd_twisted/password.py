from twisted.web import xmlrpc
import xmlrpclib

from siptrackdlib import password

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class PasswordTreeRPC(baserpc.BaseRPC):
    node_type = 'password tree'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid):
        """Create a new password tree."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'password tree')
        return obj.oid

class PasswordCategoryRPC(baserpc.BaseRPC):
    node_type = 'password category'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid):
        """Create a new password category."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'password category')
        return obj.oid

class PasswordRPC(baserpc.BaseRPC):
    node_type = 'password'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, password, key_oid = ''):
        """Create a new password."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        if len(key_oid) == 0:
            key = None
        else:
            key = self.object_store.getOID(key_oid, user = self.user)
        passwd = parent.add(self.user, 'password', password, key)
        return passwd.oid


    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_password(self, oid, new_password):
        """Change a Passwords password."""
        password = self.getOID(oid)
        password.setPassword(self.user, new_password)
        return True

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_password_key(self, oid, new_password_key_oid):
        """Change a Passwords password key."""
        password = self.getOID(oid)
        new_password_key = None
        if new_password_key_oid:
            new_password_key = self.object_store.getOID(new_password_key_oid, 'password key', self.user)
        password.setPasswordKey(self.user, new_password_key)
        return True

class PasswordKeyRPC(baserpc.BaseRPC):
    node_type = 'password key'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, key):
        """Create a new password key."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        pk = parent.add(self.user, 'password key', key)
        return pk.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_change_key(self, oid, new_key):
        """Change a password keys key."""
        pk = self.getOID(oid)
        pk.changeKey(new_key)
        return True

class SubKeyRPC(baserpc.BaseRPC):
    node_type = 'subkey'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_delete(self, oid):
        """Delete a subkey."""
        subkey = self.object_store.getOID(oid, 'subkey', user = self.user)
        if self.session.user.user.administrator != True and \
                self.session.user.user.oid != subkey.parent.oid:
            raise errors.PermissionDenied()
        self.object_store.getOID(oid, user = self.user).delete(recursive = True)
        return True

def password_data_extractor(node, user):
    password_key = ''
    if node.password_key:
        password_key = node.password_key.oid
    password = node.getPassword(None, user)
#    if not node.unicode:
#        password = xmlrpclib.Binary(password)
    return [password, password_key]

def sub_key_data_extractor(node, user):
    if node.password_key:
        oid = node.password_key.oid
    else:
        oid = ''
    return [oid]

gatherer.node_data_registry.register(password.PasswordTree,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(password.PasswordCategory,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(password.Password,
        password_data_extractor)
gatherer.node_data_registry.register(password.PasswordKey,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(password.PublicKey,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(password.SubKey,
        sub_key_data_extractor)
gatherer.node_data_registry.register(password.PendingSubKey,
        gatherer.no_data_extractor)
