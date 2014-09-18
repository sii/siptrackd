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
    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid):
        """Create a new UserManager."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'user manager local')
        return obj.oid

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_delete(self, session, oid, recursive = True):
        """Delete a node."""
        node = self.getOID(session, oid)
        node.delete(recursive)
        return True

class UserManagerLDAPRPC(baserpc.BaseRPC):
    node_type = 'user manager ldap'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid, connection_type, server, port, base_dn,
            valid_groups):
        """Create a new UserManagerLDAP."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'user manager ldap', connection_type, server, port,
                base_dn, valid_groups)
        return obj.oid

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_delete(self, session, oid, recursive = True):
        """Delete a node."""
        node = self.getOID(session, oid)
        node.delete(recursive)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_sync_users(self, session, oid, purge_missing_users):
        node = self.getOID(session, oid)
        node.syncUsers(purge_missing_users)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_connection_type(self, session, oid, connection_type):
        node = self.getOID(session, oid)
        node.setConnectionType(connection_type)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_server(self, session, oid, server):
        self.getOID(session, oid).setServer(server)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_port(self, session, oid, port):
        self.getOID(session, oid).setPort(port)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_base_dn(self, session, oid, base_dn):
        self.getOID(session, oid).setBaseDN(base_dn)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_valid_groups(self, session, oid, valid_groups):
        self.getOID(session, oid).setValidGroups(valid_groups)
        return True

class UserManagerActiveDirectoryRPC(baserpc.BaseRPC):
    node_type = 'user manager active directory'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid, server, base_dn,
            valid_groups, user_domain):
        """Create a new UserManagerActiveDirectory."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'user manager active directory', server,
                base_dn, valid_groups, user_domain)
        return obj.oid

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_delete(self, session, oid, recursive = True):
        """Delete a node."""
        node = self.getOID(session, oid)
        node.delete(recursive)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_sync_users(self, session, oid, username, password, purge_missing_users):
        node = self.getOID(session, oid)
        node.syncUsers(username, password, purge_missing_users)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_server(self, session, oid, server):
        self.getOID(session, oid).setServer(server)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_base_dn(self, session, oid, base_dn):
        self.getOID(session, oid).setBaseDN(base_dn)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_valid_groups(self, session, oid, valid_groups):
        self.getOID(session, oid).setValidGroups(valid_groups)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_user_domain(self, session, oid, user_domain):
        self.getOID(session, oid).setUserDomain(user_domain)
        return True

class BaseUserRPC(baserpc.BaseRPC):
    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid, username, password):
        """Create a new User."""
        return False

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_delete(self, session, oid):
        """Delete a User."""
        user = self.getOID(session, oid)
        user.delete(recursive = True)
        self.session_handler.killUserSessions(user)
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_username(self, session, oid, username):
        user = self.getOID(session, oid)
        node.setUsername(username)
        return True

    @helpers.ValidateSession()
    def xmlrpc_set_password(self, session, oid, new_password, old_password):
        session_user = session.user.user
        user = self.getOID(session, oid)
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        if old_password is False:
            if session_user.oid != user.oid:
                raise siptrackdlib.errors.SiptrackError('old password must be supplied')
            old_password = session.user.password
        user.setPassword(new_password, old_password)
        # Update the sessions stored password if we're
        # changing our own password.
        if session_user.oid == user.oid:
            session.user.password = new_password
        return True

    @helpers.ValidateSession()
    def xmlrpc_reset_password(self, session, oid, password):
        session_user = session.user.user
        user = self.getOID(session, oid)
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        user.resetPassword(password)
        # Update the sessions stored password if we're
        # changing our own password.
        if session_user.oid == user.oid:
            session.user.password = password
        return True

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_administrator(self, session, oid, value):
        user = self.getOID(session, oid)
        user.administrator = value
        return True

    @helpers.ValidateSession()
    def xmlrpc_connect_password_key(self, session, user_oid, pk_oid,
            user_password = False, pk_password = False):
        """Connect the user to a password key.
        """
        user = self.getOID(session, user_oid)
        session_user = session.user.user
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        if user_password is False:
            if user is session.user.user:
                user_password = session.user.password
        pk = self.object_store.getOID(pk_oid, 'password key', user = session.user)
        user.connectPasswordKey(pk, user_password, pk_password)
        return True

class UserLocalRPC(BaseUserRPC):
    node_type = 'user local'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid, username, password, administrator):
        """Create a new User."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'user local', username, password,
                administrator)
        return obj.oid

class UserLDAPRPC(BaseUserRPC):
    node_type = 'user ldap'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, *args, **kwargs):
        """Create a new User."""
        raise siptrackdlib.errors.SiptrackError('add not supported for ldap users')

    @helpers.ValidateSession()
    def xmlrpc_set_password(self, session, oid, new_password, old_password):
        session_user = session.user.user
        user = self.getOID(session, oid)
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        if old_password is False:
            old_password = None
        user.setPassword(new_password, old_password)
        return True

class UserActiveDirectoryRPC(BaseUserRPC):
    node_type = 'user active directory'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, *args, **kwargs):
        """Create a new User."""
        raise siptrackdlib.errors.SiptrackError('add not supported for active directory users')

    @helpers.ValidateSession()
    def xmlrpc_set_password(self, session, oid, new_password, old_password):
        session_user = session.user.user
        user = self.getOID(session, oid)
        if session_user.administrator != True and \
                session_user.oid != user.oid:
            raise errors.PermissionDenied()
        if old_password is False:
            old_password = None
        user.setPassword(new_password, old_password)
        return True

class UserGroupRPC(baserpc.BaseRPC):
    node_type = 'user group'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid, users):
        """Create a new UserGroup."""
        parent = self.object_store.getOID(parent_oid, user = session.user)
        users = [self.object_store.getOID(oid, user = session.user) for oid in \
                users]
        obj = parent.add(session.user, 'user group', users)
        return obj.oid

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_set_users(self, session, oid, users):
        node = self.getOID(session, oid)
        users = [self.object_store.getOID(oid, ['user local', 'user ldap'], user = session.user) for oid in users]
        node.users.set(users)
        return True

class UserGroupLDAPRPC(baserpc.BaseRPC):
    node_type = 'user group ldap'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid, users):
        """Don't create a new UserGroup."""
        raise siptrackdlib.errors.SiptrackError('add not supported for LDAP groups')

class UserGroupActiveDirectoryRPC(baserpc.BaseRPC):
    node_type = 'user group ldap'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid, users):
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
