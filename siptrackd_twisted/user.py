from twisted.web import xmlrpc

from siptrackdlib import user
import siptrackdlib.errors

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class UserRPC(baserpc.BaseRPC):
    pass

class UserManagerRPC(baserpc.BaseRPC):
    pass

class UserManagerLocalRPC(baserpc.BaseRPC):
    node_type = 'user manager local'
    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, parent_oid):
        """Create a new UserManager."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'user manager local')
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_delete(self, oid, recursive = True):
        """Delete a node."""
        node = self.getOID(oid)
        node.delete(recursive)
        return True

class UserManagerLDAPRPC(baserpc.BaseRPC):
    node_type = 'user manager ldap'

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, parent_oid, connection_type, server, port, base_dn,
            valid_groups):
        """Create a new UserManagerLDAP."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'user manager ldap', connection_type, server, port,
                base_dn, valid_groups)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_delete(self, oid, recursive = True):
        """Delete a node."""
        node = self.getOID(oid)
        node.delete(recursive)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_sync_users(self, oid, purge_missing_users):
        node = self.getOID(oid)
        node.syncUsers(purge_missing_users)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_connection_type(self, oid, connection_type):
        node = self.getOID(oid)
        node.setConnectionType(connection_type)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_server(self, oid, server):
        self.getOID(oid).setServer(server)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_port(self, oid, port):
        self.getOID(oid).setPort(port)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_base_dn(self, oid, base_dn):
        self.getOID(oid).setBaseDN(base_dn)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_valid_groups(self, oid, valid_groups):
        self.getOID(oid).setValidGroups(valid_groups)
        return True

class UserManagerActiveDirectoryRPC(baserpc.BaseRPC):
    node_type = 'user manager active directory'

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, parent_oid, server, base_dn,
            valid_groups, user_domain):
        """Create a new UserManagerActiveDirectory."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'user manager active directory', server,
                base_dn, valid_groups, user_domain)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_delete(self, oid, recursive = True):
        """Delete a node."""
        node = self.getOID(oid)
        node.delete(recursive)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_sync_users(self, oid, username, password, purge_missing_users):
        node = self.getOID(oid)
        node.syncUsers(username, password, purge_missing_users)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_server(self, oid, server):
        self.getOID(oid).setServer(server)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_base_dn(self, oid, base_dn):
        self.getOID(oid).setBaseDN(base_dn)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_valid_groups(self, oid, valid_groups):
        self.getOID(oid).setValidGroups(valid_groups)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_user_domain(self, oid, user_domain):
        self.getOID(oid).setUserDomain(user_domain)
        return True

class BaseUserRPC(baserpc.BaseRPC):
    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, parent_oid, username, password):
        """Create a new User."""
        return False

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_delete(self, oid):
        """Delete a User."""
        user = self.getOID(oid)
        user.delete(recursive = True)
        self.session_handler.killUserSessions(user)
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_username(self, oid, username):
        user = self.getOID(oid)
        node.setUsername(username)
        return True

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_password(self, oid, new_password, old_password):
        session_user = self.session.user.user
        user = self.getOID(oid)
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        if old_password is False:
            if session_user.oid != user.oid:
                raise siptrackdlib.errors.SiptrackError('old password must be supplied')
            old_password = self.session.user.password
        user.setPassword(new_password, old_password)
        # Update the sessions stored password if we're
        # changing our own password.
        if session_user.oid == user.oid:
            self.session.user.password = new_password
        return True

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_reset_password(self, oid, password):
        session_user = self.session.user.user
        user = self.getOID(oid)
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        user.resetPassword(password)
        # Update the sessions stored password if we're
        # changing our own password.
        if session_user.oid == user.oid:
            self.session.user.password = password
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_administrator(self, oid, value):
        user = self.getOID(oid)
        user.administrator = value
        return True

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_connect_password_key(self, user_oid, pk_oid,
            user_password = False, pk_password = False):
        """Connect the user to a password key.
        """
        user = self.getOID(user_oid)
        session_user = self.session.user.user
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        if user_password is False:
            if user is self.session.user.user:
                user_password = self.session.user.password
        pk = self.object_store.getOID(pk_oid, 'password key', user = self.user)
        user.connectPasswordKey(pk, user_password, pk_password)
        return True

class UserLocalRPC(BaseUserRPC):
    node_type = 'user local'

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, parent_oid, username, password, administrator):
        """Create a new User."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        obj = parent.add(self.user, 'user local', username, password,
                administrator)
        return obj.oid

class UserLDAPRPC(BaseUserRPC):
    node_type = 'user ldap'

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, *args, **kwargs):
        """Create a new User."""
        raise siptrackdlib.errors.SiptrackError('add not supported for ldap users')

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_password(self, oid, new_password, old_password):
        session_user = self.session.user.user
        user = self.getOID(oid)
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        if old_password is False:
            old_password = None
        user.setPassword(new_password, old_password)
        return True

class UserActiveDirectoryRPC(BaseUserRPC):
    node_type = 'user active directory'

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, *args, **kwargs):
        """Create a new User."""
        raise siptrackdlib.errors.SiptrackError('add not supported for active directory users')

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_set_password(self, oid, new_password, old_password):
        session_user = self.session.user.user
        user = self.getOID(oid)
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        if old_password is False:
            old_password = None
        user.setPassword(new_password, old_password)
        return True

class UserGroupRPC(baserpc.BaseRPC):
    node_type = 'user group'

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, parent_oid, users):
        """Create a new UserGroup."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        users = [self.object_store.getOID(oid, user = self.user) for oid in \
                users]
        obj = parent.add(self.user, 'user group', users)
        return obj.oid

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_users(self, oid, users):
        node = self.getOID(oid)
        users = [self.object_store.getOID(oid, ['user local', 'user ldap'], user = self.user) for oid in users]
        node.users.set(users)
        return True

class UserGroupLDAPRPC(baserpc.BaseRPC):
    node_type = 'user group ldap'

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, parent_oid, users):
        """Don't create a new UserGroup."""
        raise siptrackdlib.errors.SiptrackError('add not supported for LDAP groups')

class UserGroupActiveDirectoryRPC(baserpc.BaseRPC):
    node_type = 'user group ldap'

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_add(self, parent_oid, users):
        """Don't create a new UserGroup."""
        raise siptrackdlib.errors.SiptrackError('add not supported for active directory groups')

def user_group_extractor(node, user):
    users = [u.oid for u in node.users.get()]
    return [users]

def user_extractor(node, user):
    return [node._username.get(), node.administrator]

def user_manager_ldap_extractor(node, user):
    data = []
    data.append(node._connection_type.get())
    data.append(node._server.get())
    data.append(node._port.get())
    data.append(node._base_dn.get())
    data.append(node._valid_groups.get())
    return data

def user_manager_active_directory_extractor(node, user):
    data = []
    data.append(node._server.get())
    data.append(node._base_dn.get())
    data.append(node._valid_groups.get())
    data.append(node._user_domain.get())
    return data

gatherer.node_data_registry.register(user.UserManagerLocal,
        gatherer.no_data_extractor)
gatherer.node_data_registry.register(user.UserManagerLDAP,
        user_manager_ldap_extractor)
gatherer.node_data_registry.register(user.UserManagerActiveDirectory,
        user_manager_active_directory_extractor)
gatherer.node_data_registry.register(user.UserLocal,
        user_extractor)
gatherer.node_data_registry.register(user.UserLDAP,
        user_extractor)
gatherer.node_data_registry.register(user.UserActiveDirectory,
        user_extractor)
gatherer.node_data_registry.register(user.UserGroup,
        user_group_extractor)
gatherer.node_data_registry.register(user.UserGroupLDAP,
        user_group_extractor)
gatherer.node_data_registry.register(user.UserGroupActiveDirectory,
        user_group_extractor)
