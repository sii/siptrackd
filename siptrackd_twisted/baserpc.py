import xmlrpclib
from twisted.web import xmlrpc
import twisted.python
from twisted.internet import threads
from twisted.internet import defer

from siptrackd_twisted import log
from siptrackd_twisted import helpers

class BaseRPC(xmlrpc.XMLRPC):
    def __init__(self, object_store, session_handler):
        xmlrpc.XMLRPC.__init__(self)
        self.object_store = object_store
        self.session_handler = session_handler
        self.session = None

    def _get_view_tree(self):
        return self.object_store.view_tree
    def _set_view_tree(self, val):
        pass
    view_tree = property(_get_view_tree, _set_view_tree)

    def getOID(self, oid):
        return self.object_store.getOID(oid, self.node_type, user = self.user)

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_add(self, parent_oid, *args, **kwargs):
        """Create a new node."""
        parent = self.object_store.getOID(parent_oid, user = self.user)
        node = parent.add(self.user, self.node_type, *args, **kwargs)
        return node.oid

    @helpers.error_handler
    @helpers.validate_session
    def xmlrpc_delete(self, oid, recursive = True):
        """Delete a node."""
        node = self.getOID(oid)
        node.delete(recursive, self.user)
        return True

    @defer.inlineCallbacks
    def _cbRender(self, result, request, responseFailed=None): 
        """Override method to do threaded xmlrpclib.dump.

        This is ugly and non-portable, but will have to do for now.
        """
        if responseFailed: 
            return 
 
        if isinstance(result, xmlrpc.Handler): 
            result = result.result 
        if not isinstance(result, xmlrpc.Fault):
            result = (result,)
        try:
            try:
                content = yield self.threadDumpResult(result)
            except Exception, e:
                f = xmlrpc.Fault(self.FAILURE, "Can't serialize output: %s" % (e,))
                content = xmlrpclib.dumps(f, methodresponse=True,
                                          allow_none=self.allowNone)

            request.setHeader("content-length", str(len(content)))
            request.write(content)
        except:
            twisted.python.log.err()
        request.finish()

    def threadDumpResult(self, *args, **kwargs):
        """Threaded xmlrpclib.dumps."""
        return threads.deferToThread(self._threadDumpResult, *args, **kwargs)

    def _threadDumpResult(self, data):
        if data is None:
            data = self.prepared_data
        data = data
        content = xmlrpclib.dumps(
            data, methodresponse=True,
            allow_none=self.allowNone)
        return content

