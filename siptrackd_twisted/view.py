from twisted.web import xmlrpc

from siptrackdlib import view

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc

class ViewTreeRPC(baserpc.BaseRPC):
    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_get_user_manager(self):
        """Get the default user manager."""
        return self.view_tree.user_manager.oid

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_set_user_manager(self, user_manager_oid):
        """Set the default user manager.
        
        This will also terminate all current sessions.
        """
        um = self.object_store.getOID(user_manager_oid,
                ['user manager local', 'user manager ldap', 'user manager active directory'], user = self.user)
        self.view_tree.user_manager = um
        self.session_handler.killAllSessions()
        return True

    @helpers.error_handler
    @helpers.validate_session
    @helpers.require_admin
    def xmlrpc_delete(self):
        return False

class ViewRPC(baserpc.BaseRPC):
    node_type = 'view'

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self):
        """Create a new view."""
        obj = self.view_tree.add(self.user, 'view')
        return obj.oid

def view_tree_data_extractor(node, user):
    return [node.user_manager.oid]

gatherer.node_data_registry.register(view.ViewTree,
        view_tree_data_extractor)
gatherer.node_data_registry.register(view.View,
        gatherer.no_data_extractor)
