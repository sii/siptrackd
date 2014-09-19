from twisted.internet import defer

from siptrackdlib import objecttree
from siptrackdlib import treenodes
from siptrackdlib import view
from siptrackdlib import password
from siptrackdlib import errors
from siptrackdlib import search
from siptrackdlib import log
from siptrackdlib.objectregistry import object_registry

STORE_VERSION = '1'

tree_callbacks = {
        'load_data': treenodes.load_data_callback,
        'remove': treenodes.remove_callback,
        'relocate': treenodes.relocate_callback
}

class ObjectStore(object):
    def __init__(self, storage, preload = True, searcher = None):
        self.preload = preload
        self.storage = storage
        self.searcher = searcher
        if not searcher:
            self.searcher = search.MemorySearch()

    @defer.inlineCallbacks
    def init(self):
        yield self._checkStorage()
        self._last_oid = yield self._getLastOID()
        self.call_loaded = True
        self.oid_class_mapping = yield self._loadOIDClassMapping()
        self.object_tree = objecttree.Tree(tree_callbacks, self)
        self.object_registry = object_registry
        if not self.storage.OIDExists('0'):
            # FIXME: with a global object registry things break down if
            # someone tries to create multiple object stores. -- The oid
            # allocator specifically. This should be fixed.
            object_registry.next_oid = 0
            self.view_tree = object_registry.createObject(
                    view.ViewTree.class_id, self.object_tree)
            self.storage.addOID('ROOT', self.view_tree.oid,
                    view.ViewTree.class_id)
            self.oid_class_mapping[self.view_tree.oid] = view.ViewTree.class_id
        else:
            yield self._populateObjectTree()
            self.view_tree = self.getOID('0')
        object_registry.next_oid = self._getNextOID()
        if preload:
            yield self.preLoad()
        self.event_triggers_enabled = True
        self.event_triggers = list(self.view_tree.listChildren(include = ['event trigger']))
        yield self.view_tree._initUserManager()
        if self.searcher:
            self.searcher._buildIndex(self)

    @defer.inlineCallbacks
    def reload(self):
        """Reload an object store.

        Reload the object store from the backend, dropping all cached
        nodes.
        """
        self.object_tree.free()
        self.storage.reload()
        self.oid_class_mapping = yield self._loadOIDClassMapping()
        self.object_tree = objecttree.Tree(tree_callbacks, self)
        yield self._populateObjectTree()
        self.view_tree = self.getOID('0')
        if self.preload:
            yield self.preLoad()
        yield self.view_tree._initUserManager()
        treenodes.perm_cache.clear()

    def _checkStorage(self):
        self.storage.initialize(STORE_VERSION)
        current_version = self.storage.getVersion()
        if current_version != STORE_VERSION:
            error = 'Wanted storage version %s, got version %s, try upgrading.' % (
                    STORE_VERSION, current_version)
            raise errors.InvalidStorageVersion(error)
        defer.succeed(True)

    def preLoad(self):
        """Preload node data.

        The following happens:
          * All node data is grabbed from storage.
          * The object tree is walked grabbing ext_data from each bran
            which causes the node to load (but it's _loaded method is
            node called due to ObjectStore.call_loaded not being set.
          * The nodes data is passed to it via it's _loaded method.
            The node is free to do whatever it likes with the data,
            several node types currently don't have a _loaded method
            despite the fact that they have storage data. They should
            really be added.
        If no data exists for the oid an empty dict is passed in.
        The layout of the data passed to the node is a dict of one or
        more of:
        data['storage_data_name] = (data_type, data)
        """
        data_mapping = {}
        for oid, data_name, data in self.storage.iterOIDData():
            if oid not in data_mapping:
                data_mapping[oid] = {}
            data_mapping[oid][data_name] = data

        self.call_loaded = False
        try:
            for branch in self.object_tree.traverse():
                if branch.hasExtData():
                    continue
                node = branch.ext_data
                if not node:
                    log.msg('ObjectStore.preLoad branch %s returned no ext_data node, skipping' % (branch))
                    continue
                data = {}
                if branch.oid in data_mapping:
                    data = data_mapping[branch.oid]
                # Calling _loaded must be done with call_loaded enabled.
                # This is due to the possibility that a nodes _loaded
                # will use getOID to fetch another node which might not
                # have been loaded yet. If that happens with call_loaded =
                # False the node will be loaded without ever having
                # _loaded called, which might be very bad.
                self.call_loaded = True
                node._loaded(data)
                self.call_loaded = False
        finally:
            self.call_loaded = True
        return defer.succeed(True)

    def _loadOIDClassMapping(self):
        """Return a mapping (dict) of oid -> class_id.

        The ObjectStore keeps a dict of oid to class_id mappings.
        This is done to avoid hitting storage every time a node needs
        to be loaded. When loading a node only the oid is known (from the
        branch), so the class_id needs to be looked up.
        """
        mapping = {}
        for oid, class_id in self.storage.listOIDClasses():
            mapping[oid] = class_id
        return defer.succeed(mapping)

    def _getLastOID(self):
        """Return the latest allocated OID.

        Checks the object id's allocated in storage and returns the
        highest.
        """
        last_oid = 0
        for parent_oid, oid in self.storage.listOIDs():
            oid = int(oid)
            if oid > last_oid:
                last_oid = oid
        return defer.succeed(last_oid)

    def _getNextOID(self):
        """Return the next available object id.

        Checks the object id's allocated in storage and returns the
        next available one.
        """
        self._last_oid += 1
        return self._last_oid

    def _populateObjectTree(self):
        """Populate the object tree with oids.

        Grabs all existing oids from storage and loads them into the
        object tree (a branch is created per oid.
        Also loads all associations.
        """
        oids = self.storage.listOIDs()
        self.object_tree.loadBranches(oids)
        associations = self.storage.listAssociations()
        self.object_tree.loadAssociations(associations)
        return defer.succeed(True)

    def getOID(self, oid, valid_types = None, user = None):
        """Return the object with the given object id.

        Returns actual objects, not tree.branches.
        valid_type can be either a string with a class name or a
        list of class name strings. If set the returned node must
        be one of the given types.
        """
        branch = self.object_tree.getBranch(oid)
        if not branch:
            raise errors.NonExistent("object doesn\'t exist: %s(%s)" % (type(oid), oid))
        if valid_types in [str, unicode]:
            valid_types = [valid_types]
        if valid_types:
            if branch.ext_data.class_name not in valid_types:
                raise errors.NonExistent('invalid node type')
        if user and not branch.ext_data.hasReadPermission(user):
            raise errors.PermissionDenied()
        return branch.ext_data

    def quicksearch(self, search_pattern, attr_limit = [], include = [], exclude = [], user = None,
                   fuzzy = True, default_fields = [], max_results = None):
        """Quick search for text strings.

        Uses the searcher interface from search.py.
        
        search_pattern : text pattern to search for.
        include    : include only node types listed
        exclude    : exclude node types listed
        """
        if not self.searcher:
            raise errors.SiptrackError('no searcher selected, quicksearch unavailable')
        returned = {}
        count = 0
        for oid in self.searcher.search(search_pattern, fuzzy, default_fields, max_results=None):
            try:
                node = self.getOID(oid)
            except errors.NonExistent:
                log.msg('quicksearch matched non-existent oid, something is wrong: %s' % (oid))
                continue
            if node.class_name in ['attribute', 'versioned attribute']:
                if len(attr_limit) > 0 and node.name not in attr_limit:
                    continue
                # Get the attributes nearest _non-attribute_ parent.
                node = node.getParentNode()
            if not node.hasReadPermission(user):
                continue
            if node.oid in returned:
                continue
            if len(include) > 0 and node.class_name not in include:
                continue
            if node.class_name in exclude:
                continue
            returned[node.oid] = True
            if max_results and count >= max_results:
                break
            count += 1
            yield node

    def triggerEvent(self, event_type, *event_args, **event_kwargs):
        # Don't trigger any more events while in an event trigger,
        # otherwise we could end up in a nasty loop.
        # This means that no triggers will ever be run from what
        # happens inside a trigger (node creation etc).
        if not self.event_triggers_enabled:
            return
        self.event_triggers_enabled = False
        # Make sure trigger failures don't affect anything else.
        try:
            for event_trigger in self.event_triggers:
                event_trigger.triggerEvent(event_type, *event_args, **event_kwargs)
        except Exception, e:
            log.msg('Trigger %s raised unhandled exception: %s' % (event_trigger, str(e)))
        self.event_triggers_enabled = True

    def commit(self, nodes):
        if type(nodes) not in [list, tuple]:
            nodes = [nodes]
        for node in nodes:
            if node._storage_actions:
                actions = node._storage_actions
                node._storage_actions = []
                for action in actions:
                    args = action['args']
                    if action['action'] == 'create_node':
                        parent_oid = ''
                        parent = node.parent
                        if parent:
                            parent_oid = parent.oid
                        self.storage.addOID(parent_oid, node.oid, node.class_id)
                    elif action['action'] == 'remove_node':
                        self.storage.removeOID(node.oid)
                    elif action['action'] == 'relocate':
                        self.storage.relocate(node.oid, node.branch.parent.oid)
                    elif action['action'] == 'associate':
                        self.storage.associate(node.oid, args['other'])
                    elif action['action'] == 'disassociate':
                        self.storage.disassociate(node.oid, args['other'])
                    elif action['action'] == 'write_data':
                        self.storage.writeData(node.oid, args['name'], args['value'])
        return defer.succeed(True)
