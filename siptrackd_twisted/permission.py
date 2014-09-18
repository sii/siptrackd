from twisted.web import xmlrpc

from siptrackdlib import permission

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class PermissionRPC(baserpc.BaseRPC):
    node_type = 'permission'

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_add(self, session, parent_oid, read_access, write_access, users, groups,
            all_users, recursive):
        """Create a new permission."""
        users = [self.object_store.getOID(oid, user = session.user) for oid in users]
        groups = [self.object_store.getOID(oid, user = session.user) for oid in groups]
        parent = self.object_store.getOID(parent_oid, user = session.user)
        obj = parent.add(session.user, 'permission', read_access, write_access,
                users, groups, all_users, recursive)
        return obj.oid

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_delete(self, session, oid, recursive = True):
        """Delete a node."""
        node = self.getOID(session, oid)
        node.delete(recursive)
        return True

def permission_data_extractor(node, user):
    users = [user.oid for user in node.users.get()]
    groups = [group.oid for group in node.groups.get()]
    return [node.read_access.get(), node.write_access.get(),
            users, groups, node.all_users.get(),
            node.recursive.get()]

gatherer.node_data_registry.register(permission.Permission,
        permission_data_extractor)

