from twisted.web import xmlrpc
from twisted.internet import defer

from siptrackdlib import view

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class ViewTreeRPC(baserpc.BaseRPC):
    @helpers.ValidateSession()
    def xmlrpc_get_user_manager(self, session):
        """Get the default user manager."""
        return self.view_tree.user_manager.oid

    @helpers.ValidateSession(require_admin=True)
    @defer.inlineCallbacks
    def xmlrpc_set_user_manager(self, session, user_manager_oid):
        """Set the default user manager.
        
        This will also terminate all current sessions.
        """
        um = self.object_store.getOID(user_manager_oid,
                ['user manager local', 'user manager ldap', 'user manager active directory'], user = session.user)
        self.view_tree.user_manager = um
        self.session_handler.killAllSessions()
        yield self.view_tree.commit()
        defer.returnValue(True)

    @helpers.ValidateSession(require_admin=True)
    def xmlrpc_delete(self, session):
        return False

class ViewRPC(baserpc.BaseRPC):
    node_type = 'view'

    @helpers.ValidateSession()
    @defer.inlineCallbacks
    def xmlrpc_add(self, session):
        """Create a new view."""
        obj = self.view_tree.add(session.user, 'view')
        yield obj.commit()
        defer.returnValue(obj.oid)

def view_tree_data_extractor(node, user):
    return [node.user_manager.oid]

gatherer.node_data_registry.register(view.ViewTree,
        view_tree_data_extractor)
gatherer.node_data_registry.register(view.View,
        gatherer.no_data_extractor)
