import hashlib
try:
    import ldap
    _have_ldap = True
except ImportError:
    _have_ldap = False

from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import attribute
from siptrackdlib import password
from siptrackdlib import errors
from siptrackdlib import storagevalue

class UserManagerLocal(treenodes.BaseNode):
    """A manager for user accounts."""
    class_id = 'UM'
    class_name = 'user manager local'

    def __init__(self, oid, branch):
        super(UserManagerLocal, self).__init__(oid, branch)

    def remove(self, recursive):
        """Overrides default treenode.remove.

        Don't permit removal of active user manager.
        """
        view_tree = self.getParent('view tree')
        if view_tree.user_manager and view_tree.user_manager.oid == self.oid:
            raise errors.SiptrackError('unable to remove active user manager')
        super(UserManagerLocal, self).remove(recursive)
    delete = remove

    def isUsernameAvailable(self, username, exclude = None):
        for user in self.listChildren(include = ['user local']):
            if user == exclude:
                continue
            if username == user._username.get():
                return False
        return True

    def login(self, username, password):
        for user in self.listChildren(include = ['user local']):
            if user._username.get() == username:
                if user.authenticate(password):
                    user._userLoggedIn(password)
                    return UserInstance(user, password)
        return None

class UserManagerLDAP(treenodes.BaseNode):
    """A manager for LDAP user accounts."""
    class_id = 'UML'
    class_name = 'user manager ldap'

    def __init__(self, oid, branch, connection_type = None,
            server = None, port = None, base_dn = None,
            valid_groups = None):
        super(UserManagerLDAP, self).__init__(oid, branch)
        self._connection_type = storagevalue.StorageValue(self, 'connection_type',
                connection_type)
        self._server = storagevalue.StorageValue(self, 'server', server)
        self._port = storagevalue.StorageValue(self, 'port', port)
        self._base_dn = storagevalue.StorageValue(self, 'base_dn', base_dn)
        self._valid_groups = storagevalue.StorageValue(self, 'valid_groups',
                valid_groups)

    def remove(self, recursive):
        """Overrides default treenode.remove.

        Don't permit removal of active user manager.
        """
        view_tree = self.getParent('view tree')
        if view_tree.user_manager and view_tree.user_manager.oid == self.oid:
            raise errors.SiptrackError('unable to remove active user manager')
        super(UserManagerLDAP, self).remove(recursive)
    delete = remove

    def _makeServerString(self):
        s = '%s://%s:%s' % (self._connection_type.get(),
                self._server.get(),
                self._port.get())
        return s

    def _created(self, user):
        super(UserManagerLDAP, self)._created(user)
        if type(self._connection_type.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid connection_type in %s object' % (self.__class__.__name__))
        if type(self._server.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid server in %s object' % (self.__class__.__name__))
        if type(self._port.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid port in %s object' % (self.__class__.__name__))
        if type(self._base_dn.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid base_dn in %s object' % (self.__class__.__name__))
        if type(self._valid_groups.get()) is not list:
            raise errors.SiptrackError('invalid valid_groups list in %s object' % (self.__class__.__name__))
        try:
            int(self._port.get())
        except ValueError:
            raise errors.SiptrackError('invalid port in %s object' % (self.__class__.__name__))
        self._connection_type.commit()
        self._server.commit()
        self._port.commit()
        self._base_dn.commit()
        self._valid_groups.commit()

    def _loaded(self, data = None):
        """Load the user information from disk."""
        super(UserManagerLDAP, self)._loaded(data)
        if data != None:
            self._connection_type.preload(data)
            self._server.preload(data)
            self._port.preload(data)
            self._base_dn.preload(data)
            self._valid_groups.preload(data)
        self._makeServerString()

    def _findUserGroups(self, ldap_con, base_dn, user_dn):
        """Return a list of all groups the given user is a member of.
        
        The DN of each group is returned.
        """
        user_groups = []
        if type(base_dn) == unicode:
            base_dn = base_dn.encode('utf-8')
        result = ldap_con.search_s(base_dn, ldap.SCOPE_SUBTREE,
                'iobjectclass=groupOfNames', ['member'])
        groups = {}
        for dn, attrs in result:
            groups[dn] = attrs['member']
            if user_dn in groups[dn]:
                user_groups.append(dn)
        recurse_groups = list(user_groups)
        checked_groups = list(user_groups)
        while recurse_groups:
            cur_group = recurse_groups.pop(0)
            for member in groups[cur_group]:
                if member in groups:
                    if member not in user_groups:
                        user_groups.append(member)
                    if member not in checked_groups:
                        recurse_groups.append(member)
                        checked_groups.append(member)
        return user_groups

    def _userInValidGroup(self, ldap_con, base_dn, user_dn, valid_groups):
        """Check that the given user_dn is a member of a group in valid_group.

        valid_group must be a list of group_dn's (or an empty list if no
        group membership is required).
        """
        if len(valid_groups) == 0:
            return True
        user_groups = self._findUserGroups(ldap_con, base_dn, user_dn)
        for user_group in user_groups:
            if user_group in valid_groups:
                return True
        return False

    def _authenticate(self, ldap_server, base_dn, username, password,
            valid_groups):
        """Authenticate a user against an LDAP server.

        Also checks that the given user is a member of one of the groups
        in 'valid_groups'. If valid_groups is empty no group membership
        is required.
        """
        ldap_con = ldap.initialize(ldap_server)
        ldap_con.simple_bind_s('', '')
        if type(base_dn) == unicode:
            base_dn = base_dn.encode('utf-8')
        try:
            search_user = 'uid=%s' % (username)
            res = ldap_con.search_s(base_dn, ldap.SCOPE_SUBTREE, search_user,
                    attrsonly = True, attrlist = ['uid'])
            if len(res) != 1:
                return None
            dn, attrs = res[0]
#            if not self._userInValidGroup(ldap_con, base_dn, dn, valid_groups):
#                return None
        finally:
            ldap_con.unbind()
        try:
            l = ldap.initialize(ldap_server)
            l.simple_bind_s(dn, password)
            l.unbind()
        except ldap.INVALID_CREDENTIALS:
            return None
        except ldap.LDAPError, e:
            return None
        return True

    def login(self, username, password):
        """Try to login with the given username and password.

        Queries the ldap server to check if the username/password is
        correct.
        Returns a UserInstance of the login was valid otherwise None.
        """
        local_user = self._getUser(username)
        if not local_user:
            return None
        ldap_server = self._makeServerString()
        user = None
        if type(username) == unicode:
            username = username.encode('utf-8')
        if type(password) == unicode:
            password = password.encode('utf-8')
        if self._authenticate(ldap_server, self._base_dn.get(),
                username, password, self._valid_groups.get()):
            user = UserInstance(local_user, password)
            local_user._userLoggedIn(password)
        return user

    def _getUser(self, username):
        """Return a UserLDAP user matching the username.

        If the user doesn't exist it's created.
        """
        for user in self.listChildren(include = ['user ldap']):
            if user._username.get() == username:
                return user
#        user = self.add(None, 'user ldap', username)
#        return user
        return None

    def _listAllLDAPUsers(self, ldap_con, base_dn):
        """Return all users on the ldap server (under base_dn)."""
        users = []
        if type(base_dn) == unicode:
            base_dn = base_dn.encode('utf-8')
        result = ldap_con.search_s(base_dn, ldap.SCOPE_SUBTREE, 'uid=*',
                attrsonly = True, attrlist = ['uid'])
        for dn, attrs in result:
            users.append(dn)
        return users

    def _listLDAPUsersInGroups(self, ldap_con, base_dn, valid_groups):
        """Return all users on the ldap server that are in one of the given groups."""
        users = []
        if type(base_dn) == unicode:
            base_dn = base_dn.encode('utf-8')
        result = ldap_con.search_s(base_dn, ldap.SCOPE_SUBTREE,
                'objectclass=groupOfNames', ['member'])
        groups = {}
        for dn, attrs in result:
            groups[dn] = attrs['member']

        recurse_groups = list(valid_groups)
        checked_groups = list(valid_groups)
        while recurse_groups:
            cur_group = recurse_groups.pop(0)
            if cur_group in groups:
                for member in groups[cur_group]:
                    if member.startswith('uid=') and member not in users:
                        users.append(member)
                    if member in groups and member not in checked_groups:
                        recurse_groups.append(member)
        return users

    def _getUserUid(self, ldap_con, user):
        """Returns a users uid based on it's dn."""
        try:
            result = ldap_con.search_s(user, ldap.SCOPE_SUBTREE)
        except Exception, e:
            return None
        if len(result) != 1:
            return None
        dn, attrs = result[0]
        if 'uid' in attrs:
            return attrs['uid'][0]
        return None

    def _validSiptrackUsers(self, ldap_con, base_dn, valid_groups):
        """Return a list of users from an ldap server that are permitted to login.

        A list of user uids is returned.
        """
        users = None
        # If all groups are valid, just return all users.
        if len(valid_groups) == 0:
            users = self._listAllLDAPUsers(ldap_con, base_dn)
        else:
            users = self._listLDAPUsersInGroups(ldap_con, base_dn, valid_groups)
        users_uid = []
        for user_dn in users:
            user_uid = self._getUserUid(ldap_con, user_dn)
            if user_uid is not None:
                users_uid.append(user_uid)
        return users_uid

    def syncUsers(self, purge_missing_users = False):
        """Create UserLDAP objects based on the users in the ldap server.

        This updates the user objects for the UserManager in siptrack
        based on the users that exist in the ldap server.
        If purge_missing_users is True locally existing UserLDAP objects
        that don't exist on the ldap server will be removed.
        """
        ldap_server = self._makeServerString()
        ldap_con = ldap.initialize(ldap_server)
        ldap_con.simple_bind_s('', '')
        try:
            ldap_users = self._validSiptrackUsers(ldap_con,
                    self._base_dn.get(), self._valid_groups.get())
        finally:
            ldap_con.unbind()
        local_users = list(self.listChildren(include = ['user ldap']))
        local_usernames = [user._username.get() for user in local_users]
        for ldap_user in ldap_users:
            if ldap_user not in local_usernames:
                self.add(None, 'user ldap', ldap_user, False)
        if purge_missing_users:
            for local_user in local_users:
                if local_user._username.get() not in ldap_users:
                    local_user.remove(recursive = True)

    def setConnectionType(self, connection_type):
        if type(connection_type) not in [unicode, str]:
            raise errors.SiptrackError('invalid connection_type in setConnectionType')
        self._connection_type.set(connection_type)

    def setServer(self, server):
        if type(server) not in [unicode, str]:
            raise errors.SiptrackError('invalid server in setServer')
        self._server.set(server)

    def setPort(self, port):
        if type(port) not in [unicode, str]:
            raise errors.SiptrackError('invalid port in setPort')
        self._port.set(port)

    def setBaseDN(self, base_dn):
        if type(base_dn) not in [unicode, str]:
            raise errors.SiptrackError('invalid base dn in setBaseDN')
        self._base_dn.set(base_dn)

    def setValidGroups(self, valid_groups):
        if type(valid_groups) is not list:
            raise errors.SiptrackError('invalid valid_groups in setValidGroups')
        self._valid_groups.set(valid_groups)

class UserManagerActiveDirectory(treenodes.BaseNode):
    """A manager for active directory (LDAP) user accounts."""
    class_id = 'UMAD'
    class_name = 'user manager active directory'

    def __init__(self, oid, branch,
            server = None, base_dn = None,
            valid_groups = None, user_domain = None):
        super(UserManagerActiveDirectory, self).__init__(oid, branch)
        self._server = storagevalue.StorageValue(self, 'server', server)
        self._base_dn = storagevalue.StorageValue(self, 'base_dn', base_dn)
        self._valid_groups = storagevalue.StorageValue(self, 'valid_groups',
                valid_groups)
        self._user_domain = storagevalue.StorageValue(self, 'user_domain', user_domain)

    def remove(self, recursive):
        """Overrides default treenode.remove.

        Don't permit removal of active user manager.
        """
        view_tree = self.getParent('view tree')
        if view_tree.user_manager and view_tree.user_manager.oid == self.oid:
            raise errors.SiptrackError('unable to remove active user manager')
        super(UserManagerActiveDirectory, self).remove(recursive)
    delete = remove

    def _makeServerString(self):
        s = 'ldap://%s:389' % (self._server.get())
        return s

    def _created(self, user):
        super(UserManagerActiveDirectory, self)._created(user)
        if type(self._server.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid server in %s object' % (self.__class__.__name__))
        if type(self._base_dn.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid base_dn in %s object' % (self.__class__.__name__))
        if type(self._valid_groups.get()) is not list:
            raise errors.SiptrackError('invalid valid_groups list in %s object' % (self.__class__.__name__))
        if type(self._user_domain.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid user_domain in %s object' % (self.__class__.__name__))
        self._server.commit()
        self._base_dn.commit()
        self._valid_groups.commit()
        self._user_domain.commit()

    def _loaded(self, data = None):
        """Load the user information from disk."""
        super(UserManagerActiveDirectory, self)._loaded(data)
        if data != None:
            self._server.preload(data)
            self._base_dn.preload(data)
            self._valid_groups.preload(data)
            self._user_domain.preload(data)
        self._makeServerString()

    def _authenticate(self, ldap_server, base_dn, username, password,
            valid_groups):
        """Authenticate a user against an LDAP server.

        Also checks that the given user is a member of one of the groups
        in 'valid_groups'. If valid_groups is empty no group membership
        is required.
        """
        try:
            ldap_con = ldap.initialize(ldap_server)
            bind_username = username
            if self._user_domain.get():
                bind_username = '%s@%s' % (username, self._user_domain.get())
            ldap_con.simple_bind_s(bind_username, password)
        except ldap.INVALID_CREDENTIALS:
            return None
        except ldap.LDAPError, e:
            return None
        if type(base_dn) == unicode:
            base_dn = base_dn.encode('utf-8')
        try:
            ldap_con.set_option(ldap.OPT_REFERRALS, 0)
            search_user = 'sAMAccountName=%s' % (username)
            res = ldap_con.search_s(base_dn, ldap.SCOPE_SUBTREE, search_user,
                    attrsonly = True, attrlist = ['distinguishedName'])
            if len(res) == 0:
                return None
            dn, attrs = res[0]
#            if not self._userInValidGroup(ldap_con, base_dn, dn, valid_groups):
#                return None
        finally:
            ldap_con.unbind()
        return True

    def login(self, username, password):
        """Try to login with the given username and password.

        Queries the ldap server to check if the username/password is
        correct.
        Returns a UserInstance of the login was valid otherwise None.
        """
        local_user = self._getUser(username)
        if not local_user:
            return None
        ldap_server = self._makeServerString()
        user = None
        if type(username) == unicode:
            username = username.encode('utf-8')
        if type(password) == unicode:
            password = password.encode('utf-8')
        if self._authenticate(ldap_server, self._base_dn.get(),
                username, password, self._valid_groups.get()):
            user = UserInstance(local_user, password)
            local_user._userLoggedIn(password)
        return user

    def _getUser(self, username):
        """Return a UserLDAP user matching the username.

        If the user doesn't exist it's created.
        """
        for user in self.listChildren(include = ['user active directory']):
            if user._username.get() == username:
                return user
        return None
#        user = self.add(None, 'user active directory', username)
#        return user

    def _validSiptrackUsers(self, ldap_con, base_dn, valid_groups):
        """Return a list of users from an ldap server that are permitted to login.

        A list of user uids is returned.
        """
        users = None
        # If all groups are valid, just return all users.
        if len(valid_groups) == 0:
            users = self._listAllLDAPUsers(ldap_con, base_dn)
        else:
            users = self._listLDAPUsersInGroups(ldap_con, base_dn, valid_groups)
        users_uid = []
        for user_dn in users:
            user_uid = self._getUserUid(ldap_con, user_dn)
            if user_uid is not None:
                users_uid.append(user_uid)
        return users_uid

    def syncUsers(self, bind_username, bind_password,
                        purge_missing_users = False):
        """Create UserActiveDirectory objects based on the users in the ldap server.

        This updates the user objects for the UserManager in siptrack
        based on the users that exist in the ldap server.
        If purge_missing_users is True locally existing UserActiveDirectory objects
        that don't exist on the ldap server will be removed.
        """
        ldap_server = self._makeServerString()
        ldap_con = ldap.initialize(ldap_server)
        ldap_con.set_option(ldap.OPT_REFERRALS, 0)
        if self._user_domain.get():
            bind_username = '%s@%s' % (bind_username, self._user_domain.get())
        ldap_con.simple_bind_s(bind_username, bind_password)
        try:
            ldap_groups = None
            valid_group_names = self._valid_groups.get()
            if valid_group_names:
                ldap_groups = self._getLDAPGroups(ldap_con, self._base_dn.get(), valid_group_names)
            ldap_users = self._getLDAPUsers(ldap_con, self._base_dn.get(), ldap_groups)
            self._syncUsers(ldap_users, purge_missing_users)
            self._syncGroups(ldap_groups, ldap_users, purge_missing_users)
        finally:
            ldap_con.unbind()

    def _syncUsers(self, ldap_users, purge_missing):
        local_users = list(self.listChildren(include = ['user active directory']))
        local_users_by_name = {}
        for local_user in local_users:
            local_users_by_name[local_user._username.get()] = local_user
        ldap_users_by_id = {}
        for ldap_user in ldap_users.itervalues():
            ldap_users_by_id[ldap_user['id']] = ldap_user
            local_user = local_users_by_name.get(ldap_user['id'], None)
            if not local_user:
                local_user = self.add(None, 'user active directory', ldap_user['id'], False)
            ldap_user['local_user'] = local_user
        if purge_missing:
            for local_user in local_users:
                if local_user._username.get() not in ldap_users_by_id:
                    local_user.remove(recursive = True)

    def _getLDAPGroups(self, ldap_con, base_dn, valid_group_names):
        """Return all valid LDAP groups."""
        if not valid_group_names:
            return {}
        valid_group_names = list(valid_group_names)
        valid_groups = {}
        all_groups = {}
        if type(base_dn) == unicode:
            base_dn = base_dn.encode('utf-8')
        result = ldap_con.search_s(base_dn, ldap.SCOPE_SUBTREE,
                'objectclass=group', ['member', 'cn'])
        for dn, attrs in result:
            if dn:
                cn = attrs.get('cn', [])
                if len(cn) == 1 and len(cn[0]) > 0:
                    cn = cn[0]
                    members = attrs.get('member', [])
                    group = {'dn': dn, 'cn': cn, 'members': members, 'users': [], 'groups': []}
                    all_groups[dn] = group
                    if dn in valid_group_names or cn in valid_group_names:
                        valid_groups[dn] = group
        for dn, group in all_groups.iteritems():
            for member in group['members']:
                if member in all_groups:
                    group['groups'].append(member)
                else:
                    group['users'].append(member)
            del group['members']
        updated = True
        while updated:
            updated = False
            more_valid_groups = {}
            for dn, group in valid_groups.iteritems():
                for subgroup in group['groups']:
                    if subgroup in all_groups and subgroup not in valid_groups and subgroup not in more_valid_groups:
                        more_valid_groups[subgroup] = all_groups[subgroup]
                        updated = True
                group['groups'] = []
            valid_groups.update(more_valid_groups)
        return valid_groups

    def _getLDAPUsers(self, ldap_con, base_dn, valid_groups):
        """Return all (valid siptrack) users on the ldap server (under base_dn)."""
        if type(base_dn) == unicode:
            base_dn = base_dn.encode('utf-8')
        result = ldap_con.search_s(base_dn, ldap.SCOPE_SUBTREE, 'objectClass=user',
                attrsonly = False, attrlist = ['sAMAccountName'])
        group_users = None
        if valid_groups is not None:
            group_users = {}
            for group in valid_groups.itervalues():
                for user_dn in group['users']:
                    group_users[user_dn] = True
        valid_users = {}
        for dn, attrs in result:
            if not dn:
                continue
            if group_users is not None and dn not in group_users:
                continue
            name = attrs.get('sAMAccountName', [])
            if len(name) < 1 or len(name[0]) < 1:
                continue
            user = {'dn': dn, 'id': name[0] }
            valid_users[dn] = user
        return valid_users

    def _syncGroups(self, ldap_groups, ldap_users, purge_missing):
        if ldap_groups is None:
            ldap_groups = {}
        local_groups = list(self.listChildren(include = ['user group active directory']))
        local_groups_by_dn = {}
        for group in local_groups:
            local_groups_by_dn[group.getAttributeValue('dn')] = group
        for ldap_group in ldap_groups.itervalues():
            local_group = local_groups_by_dn.get(ldap_group['dn'])
            if not local_group:
                local_group = self.add(None, 'user group active directory', [])
                local_group.add(None, 'attribute', 'dn', 'text', ldap_group['dn'])
                local_group.add(None, 'attribute', 'name', 'text', ldap_group['cn'])
            ldap_group['local_group'] = local_group
        if purge_missing:
            for local_group in local_groups:
                if local_group.getAttributeValue('dn') not in ldap_groups:
                    local_group.remove(recursive = True)
        for ldap_group in ldap_groups.itervalues():
            self._syncGroupUsers(ldap_group, ldap_users)

    def _syncGroupUsers(self, ldap_group, ldap_users):
        new_users = []
        local_group = ldap_group['local_group']
        for username in ldap_group['users']:
            ldap_user = ldap_users.get(username)
            if not ldap_user:
                continue
            local_user = ldap_user['local_user']
            new_users.append(local_user)
        local_group.users.set(new_users)

    def setServer(self, server):
        if type(server) not in [unicode, str]:
            raise errors.SiptrackError('invalid server in setServer')
        self._server.set(server)

    def setBaseDN(self, base_dn):
        if type(base_dn) not in [unicode, str]:
            raise errors.SiptrackError('invalid base dn in setBaseDN')
        self._base_dn.set(base_dn)

    def setValidGroups(self, valid_groups):
        if type(valid_groups) is not list:
            raise errors.SiptrackError('invalid valid_groups in setValidGroups')
        self._valid_groups.set(valid_groups)

    def setUserDomain(self, user_domain):
        if type(user_domain) not in [str, unicode]:
            raise errors.SiptrackError('invalid user_domain in setUserDomain')
        self._user_domain.set(user_domain)

class UserCommon(object):
    def resetPasswordDependencies(self, new_password):
        """Reset everything that depends on the users password."""
        for subkey in list(self.listChildren(include = ['subkey'])):
            subkey.delete(recursive = True)
        pk = self.resetPasswordKey(new_password)
        self.connectPasswordKey(pk, new_password, new_password)
        pk = self.resetPublicKey(new_password)
        self.resetPendingSubKeys()

    def updatePasswordDependencies(self, old_password, new_password):
        for subkey in list(self.listChildren(include = ['subkey'])):
            subkey.changePassword(old_password, new_password)
        pk = self.getPasswordKey()
        if pk:
            pk.changePassword(old_password, new_password)
        else:
            self.resetPasswordKey(new_password)
        self.resetPendingSubKeys()

    def getPasswordKey(self):
        for pk in self.listChildren(include = ['password key']):
            if pk.getAttributeValue('default') == True:
                return pk
        return None

    def resetPasswordKey(self, password):
        pk = self.getPasswordKey()
        if pk:
            pk.delete(recursive = True)
        pk = self.add(None, 'password key', password)
        pk.add(None, 'attribute', 'default', 'bool', True)
        self.resetPublicKey(password)
        return pk

    def getPublicKey(self):
        for pk in self.listChildren(include = ['public key']):
            if pk.getAttributeValue('default') == True:
                return pk
        return None

    def resetPublicKey(self, password):
        pk = self.getPublicKey()
        if pk:
            pk.delete(recursive = True)
        pk = self.add(None, 'public key', self.getPasswordKey(), password)
        pk.add(None, 'attribute', 'default', 'bool', True)
        return pk

    def runPendingSubKeys(self, password):
        for psk in list(self.listChildren(include = ['pending subkey'])):
            # Don't pass on errors if this fails, it would abort the login.
            try:
                psk.connectPasswordKey(self, password, remove_self = False)
            except:
                pass
            finally:
                psk.remove(recursive = True)

    def resetPendingSubKeys(self):
        for psk in list(self.listChildren(include = ['pending subkey'])):
            psk.remove(recursive=True)

    def passwordKeyIsConnected(self, password_key, include_pending):
        include = ['subkey']
        if include_pending:
            include.append('pending subkey')
        for subkey in self.listChildren(include = include):
            if subkey.password_key == password_key:
                return True
        return False

    def connectPasswordKey(self, password_key, user_password, pk_password):
        """Enable automatic unlocking of a password key when a user logs in.
        
        password_key is a password key instance
        user_password is the users actual password

        The password key must be unlocked for this call to work.
        """
        if self.passwordKeyIsConnected(password_key, include_pending=True):
            return
        if not password_key.isValidPassword(pk_password):
            raise errors.SiptrackError('invalid password key password')
        if user_password is not False:
            if not self.authenticate(user_password):
                raise errors.SiptrackError('invalid user password when connecting password key')
            self.add(None, 'subkey', password_key, user_password, pk_password)
        else: 
            pk = self.getPublicKey()
            if not pk:
                raise errors.SiptrackError('No public key found for user, the public key will be created the first time the user logs in to siptrack.')
            self.add(None, 'pending subkey', password_key, pk_password, pk)

    def _userInit(self, password):
        """Stuff to do when a user has logged in and it's password is availble."""
        # Create the users password key if it doesn't exist.
        if not self.getPasswordKey():
            self.resetPasswordKey(password)
        if not self.getPublicKey():
            self.resetPublicKey(password)
        self.runPendingSubKeys(password)
        return True

class UserLocal(treenodes.BaseNode, UserCommon):
    """A user account."""
    class_id = 'U'
    class_name = 'user local'

    def __init__(self, oid, branch, username = None, password = None,
            administrator = None):
        super(UserLocal, self).__init__(oid, branch)
        self._username = storagevalue.StorageValue(self, 'username', username)
        self._password = storagevalue.StorageValue(self, 'password', password)
        self._administrator = storagevalue.StorageBool(self, 'administrator',
                administrator)

    def _encryptPassword(self, password):
        return hashlib.sha1(password).hexdigest()

    def _created(self, user):
        super(UserLocal, self)._created(user)
        if type(self._username.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid username in User object')
        if type(self._password.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid password in User object')
        if not self.getParent('user manager local').\
                isUsernameAvailable(self._username.get(), exclude = self):
            raise errors.SiptrackError('sorry, that username is already in use')
        self._username.commit()
        self._password.set(self._encryptPassword(self._password.get()))
        self._administrator.commit()

    def _loaded(self, data = None):
        """Load the user information from disk."""
        super(UserLocal, self)._loaded(data)
        if data != None:
            self._username.preload(data)
            self._password.preload(data)
            self._administrator.preload(data)

    def setUsername(self, username):
        if type(username) not in [unicode, str]:
            raise errors.SiptrackError('invalid username in User.setUsername')
        if not self.getParent('user manager local').isUsernameAvailable(username):
            raise errors.SiptrackError('sorry, that username is already in use')
        self._username.set(username)

    def _setPassword(self, password):
        self._password.set(self._encryptPassword(password))

    def setPassword(self, new_password, old_password):
        """Set a new password for a user.

        This is a bit iffy. Unless the user is setting a new password for
        himself we won't be able to access the password keys in his subkeys.
        If we can't reset the passwords on the subkeys, we simply remove them,
        not nice, but the best we can do.
        """
        if type(new_password) not in [unicode, str] or type(old_password) not in [unicode, str]:
            raise errors.SiptrackError('invalid password in User.setPassword')
        if not self.authenticate(old_password):
            raise errors.SiptrackError('invalid password in User.setPassword')
        self.updatePasswordDependencies(old_password, new_password)
        self._setPassword(new_password)

    def resetPassword(self, new_password):
        """Reset a users password.

        This will remove all old subkeys and other password dependent 
        stuff.
        """
        if type(new_password) not in [unicode, str]:
            raise errors.SiptrackError('invalid password in User.setPassword')
        self.resetPasswordDependencies(new_password)
        self._setPassword(new_password)

    def authenticate(self, password):
        if type(password) not in [unicode, str]:
            raise errors.SiptrackError('invalid password in User.validatePassword')
        if self._encryptPassword(password) == self._password.get():
            return True
        return False

    def _userLoggedIn(self, password):
        self._userInit(password)

    def _get_administrator(self):
        return self._administrator.get()
    def _set_administrator(self, val):
        self._administrator.set(val)
    administrator = property(_get_administrator, _set_administrator)

class UserLDAP(treenodes.BaseNode, UserCommon):
    """An LDAP user account."""
    class_id = 'UL'
    class_name = 'user ldap'

    def __init__(self, oid, branch, username = None, administrator = None):
        super(UserLDAP, self).__init__(oid, branch)
        self._username = storagevalue.StorageValue(self, 'username', username)
        self._administrator = storagevalue.StorageBool(self, 'administrator',
                administrator)
        self._password_hash = storagevalue.StorageValue(self, 'password-hash', None)

    def _created(self, user):
        super(UserLDAP, self)._created(user)
        if type(self._username.get()) not in [unicode, str]:
            raise errors.SiptrackError('invalid username in User object')
        self._username.commit()
        self._administrator.commit()

    def _loaded(self, data = None):
        """Load the user information from disk."""
        super(UserLDAP, self)._loaded(data)
        if data != None:
            self._username.preload(data)
            self._administrator.preload(data)

    def _encryptPassword(self, password):
        return hashlib.sha1(password).hexdigest()

    def _setPassword(self, password):
        self._password_hash.set(self._encryptPassword(password))

    def setUsername(self, username):
        pass

    def setPassword(self, new_password, old_password):
        """Updated a LDAP users password.

        This is used when the users password has already been changed
        in the LDAP server, it will updated subkeys etc., but will
        not actually change the users password on the LDAP server, that
        must be done by other means.

        This is a bit iffy. Unless the user is setting a new password for
        himself we won't be able to access the password keys in his subkeys.
        If we can't reset the passwords on the subkeys, we simply remove them,
        not nice, but the best we can do.
        """
        if type(new_password) not in [unicode, str] or type(old_password) not in [unicode, str]:
            raise errors.SiptrackError('invalid password in User.setPassword')
        if self._password_hash.get() != None and self._encryptPassword(old_password) != self._password_hash.get():
            raise errors.SiptrackError('invalid old password')
        self.updatePasswordDependencies(old_password, new_password)
        self._setPassword(new_password)

    def authenticate(self, password):
        if type(password) not in [unicode, str]:
            raise errors.SiptrackError('invalid password in User.authenticate')
        if self.parent.login(self._username.get(), password):
            return True
        return False

    def passwordHasChanged(self, password):
        if self._encryptPassword(password) != self._password_hash.get():
            return True
        return False

    def resetPassword(self, new_password):
        """Reset a users password.

        This will remove all old subkeys and other password dependent 
        stuff.
        """
        if type(new_password) not in [unicode, str]:
            raise errors.SiptrackError('invalid password in User.setPassword')
        self.resetPasswordDependencies(new_password)
        self._setPassword(new_password)

    def _userLoggedIn(self, password):
        # Store the hash for this (correct) password.
        if self._password_hash.get() is None:
            self._setPassword(password)
#        if self.passwordHasChanged(password):
#            self.resetPendingSubKeys()
#            self.resetPublicKey()
#            self._setPassword(password)
        self._userInit(password)

    def _get_administrator(self):
        return self._administrator.get()
    def _set_administrator(self, val):
        self._administrator.set(val)
    administrator = property(_get_administrator, _set_administrator)

class UserActiveDirectory(UserLDAP):
    """An active directory (LDAP) user account."""
    class_id = 'UAD'
    class_name = 'user active directory'

class UserGroupBase(treenodes.BaseNode):
    """Groups for users."""
    valid_user_types = []

    def __init__(self, oid, branch, users = None):
        super(UserGroupBase, self).__init__(oid, branch)
        self.users = storagevalue.StorageNodeList(self,
                'users', users, self._validateUsers)

    def _created(self, user):
        super(UserGroupBase, self)._created(user)
        self.users.commit()

    def _loaded(self, data = None):
        super(UserGroupBase, self)._loaded(data)
        self.users.preload(data)

    def _validateUsers(self, value):
        if type(value) != list:
            raise errors.SiptrackError('invalid value for user group users')
        for node in value:
            if type(node) not in self.valid_user_types:
                raise errors.SiptrackError('invalid user in group')

class UserGroup(UserGroupBase):
    """Groups for users."""
    class_id = 'UG'
    class_name = 'user group'
    valid_user_types = [UserLocal, UserLDAP, UserActiveDirectory]

class UserGroupLDAP(UserGroupBase):
    """LDAP group for users."""
    class_id = 'UGL'
    class_name = 'user group ldap'
    valid_user_types = [UserLDAP]

class UserGroupActiveDirectory(UserGroupBase):
    """LDAP group for users."""
    class_id = 'UGAD'
    class_name = 'user group active directory'
    valid_user_types = [UserActiveDirectory]

class UserInstance(object):
    class_name = 'user instance'

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.oid = user.oid

    def __str__(self):
        return '(UserInstance):%s' % (str(self.user))

    def logout(self):
        self.password = None
        self.deactivateKeys()
        self.user = None

    def getSubKeyForPasswordKey(self, password_key):
        for subkey in self.user.listChildren(include = ['subkey']):
            if subkey.password_key == password_key:
                return subkey

    def getSubkeyEncryptionStringForPasswordKey(self, password_key):
        subkey = self.getSubKeyForPasswordKey(password_key)
        ret = None
        if subkey and self.password:
            ret = subkey.getEncryptionString(self.password)
        return ret

    def _get_administrator(self):
        return self.user._administrator.get()
    def _set_administrator(self, val):
        self.user._administrator.set(val)
    administrator = property(_get_administrator, _set_administrator)

# Add the objects in this module to the object registry.
o = object_registry.registerClass(UserManagerLocal)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(UserLocal)
o.registerChild(UserGroup)

if _have_ldap:
    o = object_registry.registerClass(UserManagerLDAP)
    o.registerChild(attribute.Attribute)
    o.registerChild(attribute.VersionedAttribute)
    o.registerChild(UserLDAP)
    o.registerChild(UserGroup)
    o.registerChild(UserGroupLDAP)

    o = object_registry.registerClass(UserManagerActiveDirectory)
    o.registerChild(attribute.Attribute)
    o.registerChild(attribute.VersionedAttribute)
    o.registerChild(UserActiveDirectory)
    o.registerChild(UserGroup)
    o.registerChild(UserGroupActiveDirectory)

o = object_registry.registerClass(UserLocal)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(password.SubKey)
o.registerChild(password.PasswordKey)
o.registerChild(password.PublicKey)
o.registerChild(password.PendingSubKey)
o.registerChild(password.PasswordTree)

if _have_ldap:
    o = object_registry.registerClass(UserLDAP)
    o.registerChild(attribute.Attribute)
    o.registerChild(attribute.VersionedAttribute)
    o.registerChild(password.SubKey)
    o.registerChild(password.PasswordKey)
    o.registerChild(password.PublicKey)
    o.registerChild(password.PendingSubKey)
    o.registerChild(password.PasswordTree)

    o = object_registry.registerClass(UserActiveDirectory)
    o.registerChild(attribute.Attribute)
    o.registerChild(attribute.VersionedAttribute)
    o.registerChild(password.SubKey)
    o.registerChild(password.PasswordKey)
    o.registerChild(password.PublicKey)
    o.registerChild(password.PendingSubKey)
    o.registerChild(password.PasswordTree)

o = object_registry.registerClass(UserGroup)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

if _have_ldap:
    o = object_registry.registerClass(UserGroupLDAP)
    o.registerChild(attribute.Attribute)
    o.registerChild(attribute.VersionedAttribute)

    o = object_registry.registerClass(UserGroupActiveDirectory)
    o.registerChild(attribute.Attribute)
    o.registerChild(attribute.VersionedAttribute)
