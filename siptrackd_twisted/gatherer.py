from twisted.internet import threads
import time
import zlib
import xmlrpclib

try:
    import simplejson
    json_encode = simplejson.dumps
    json_decode = simplejson.loads
except:
    import json
    json_encode = json.dumps
    json_decode = json.loads

from siptrackdlib.objectregistry import object_registry

from siptrackd_twisted import errors
from siptrackd_twisted import log

class EntityDataCache(object):
    # Don't cache templates due to problems with their inheritance structures.
    skip_cache_data_classes = ['password', 'template', 'device template', 'network template']

    def __init__(self, node_data_registry):
        self.node_data_registry = node_data_registry
        self.cache = {}

    def _getNodeData(self, node, user):
        """Collect a nodes data into a form suitable for self.prepared_data."""
        node_data = {}
        node_data['class_id'] = node.class_id
        node_data['oid'] = node.oid
        node_data['associations'] = [a.oid for a in node.associations]
        node_data['references'] = [a.oid for a in node.references]
        node_data['data'] = self.node_data_registry.extract(node, user)
        node_data['ctime'] = node.ctime.get() or 0
        if node.parent:
            node_data['parent'] = node.parent.oid
        else:
            node_data['parent'] = ''
        node_data = json_encode(node_data)
        return node_data

    def getNodeData(self, node, user):
        ret = None
        if node.oid in self.cache:
            timestamp, data = self.cache[node.oid]
            if timestamp >= node.modtime and node.class_name not in self.skip_cache_data_classes:
                ret = data
                if node.class_name in self.skip_cache_data_classes:
                    ret['data'] = self.node_data_registry.extract(node, user)
        if not ret:
            ret = self._getNodeData(node, user)
            self.cache[node.oid] = (time.time(), ret)
        return ret

    def flush(self):
        self.cache = {}

class ListCreator(object):
    """Collect data to return to clients.

    The collected data is stored in self.prepared_data (a list).
    Each node is a dict consisting of:
        class_id: string
        oid: string
        associations: list of oid strings
        references: list of oid strings
        data: class id unique data (list)
        parent: oid string or '' if no parent exists
        ctime: creation time of the object
    """
    attr_incl = {'attribute': True, 'versioned attribute': True}

    def __init__(self, object_store, user):
        self.object_store = object_store
        self.user = user
        self.included_nodes = {}
        self.prepared_data = []
        self.runtime = 0
        self.tottime = 0

    def build(self, node, max_depth, include_parents, include_associations,
            include_references):
        """Gather data for the given oid in self.prepared_data.

            oid: the node to gather data for
            max_depth: the max depth to recurse into the tree
            include_parents: include all parents in the tree leading
                up to the given oid
        """
        data = []
        for _data in self.iterBuild([node], max_depth, include_parents, include_associations, include_references):
            data.extend(data)
        return data

    def threadBuild(self, *args, **kwargs):
        """Threaded version of build."""
        d = threads.deferToThread(self.build, *args, **kwargs)
        return d

    def iterBuild(self, nodes, max_depth, include_parents, include_associations,
            include_references):
        """Gather data for the given oid in self.prepared_data.

            oid: the node to gather data for
            max_depth: the max depth to recurse into the tree
            include_parents: include all parents in the tree leading
                up to the given oid
        """
        tot_start = time.time()
        start = time.time()
        if max_depth > -1:
            max_depth += 1
        count = 0
        data = []
        for node in nodes:
            for _data, _count in self._iterBuild(node, max_depth, include_parents,
                                        include_associations, include_references):
                count += _count
                data.extend(_data)
                if count >= 1000:
                    self.runtime += time.time() - start
                    yield self._packData(data)
                    start = time.time()
                    count = 0
                    data = []
        self.runtime += time.time() - start
        if data:
            yield self._packData(data)
        self.tottime = time.time() - tot_start
        log.debug('gatherer.iterBuild: RUNTIME: %s, TOTALTIME: %s, NODECOUNT: %s' % (self.runtime, self.tottime, len(self.included_nodes)))

    def _iterBuild(self, node, max_depth, include_parents, include_associations,
            include_references):
        count = 0
        if include_parents:
            self._addParents(node)
        associated_nodes = []
        # Special handling when gathering for an attribute specifically.
        # Otherwise fetching for an attribute can result in no data at all
        # being returned if include_parents = False.
        if node.class_name in ['attribute', 'versioned attribute']:
            exclude = []
            max_depth = 0
        for depth, child in node.traverse(max_depth = max_depth,
                include_self = True, include_depth = True, user = self.user):
            if depth == max_depth:
                if child.class_name in self.attr_incl:
                    self._addNodeAndAttributes(child)
                continue
            self._addNode(child)
            if include_associations:
                self._addAssociations(child, include_parents)
            if include_references:
                self._addReferences(child, include_parents)
            count += 1
            if count >= 1000:
                yield self.prepared_data, count
                self.prepared_data = []
                count = 0
        if self.prepared_data:
            yield self.prepared_data, count
            self.prepared_data = []

    def iterSearch(self, searcher, include_data = True,
            include_parents = True, include_associations = True,
            include_references = True):
        """Search for objects starting at oid."""
        tot_start = time.time()
        start = time.time()
        match_oids = []
        data = []
        count = 0
        for node in searcher:
            count += 1
            match_oids.append(node.oid)
            if include_data:
                for _data, _count in self._iterBuild(node, 1, include_parents,
                                                    include_associations, include_references):
                    data.extend(_data)
                    count += _count
                    if count >= 1000:
                        self.runtime += time.time() - start
                        yield self._packData([data, match_oids])
                        start = time.time()
                        match_oids = []
                        data = []
                        count = 0
            if count >= 1000:
                self.runtime += time.time() - start
                yield self._packData([data, match_oids])
                start = time.time()
                match_oids = []
                data = []
                count = 0
        self.runtime += time.time() - start
        if match_oids:
            yield self._packData([data, match_oids])
        self.tottime = time.time() - tot_start
        log.debug('gatherer.iterSearch: RUNTIME: %s, TOTALTIME: %s, NODECOUNT: %s' % (self.runtime, self.tottime, len(self.included_nodes)))

    def _packData(self, data):
        data = json_encode(data)
        data = zlib.compress(data)
        data = xmlrpclib.Binary(data)
        return data

    def _addAssociations(self, node, include_parents):
        """Add a nodes associations to prepared_data."""
        for assoc_node in node.associations:
            if include_parents:
                self._addParents(assoc_node)
            self._addNodeAndAttributes(assoc_node)

    def _addReferences(self, node, include_parents):
        """Add a nodes references to prepared_data."""
        for ref_node in node.references:
            if include_parents:
                self._addParents(ref_node)
            self._addNodeAndAttributes(ref_node)

    def _addParents(self, node):
        """Add a nodes parents to prepared_data.

        The nodes are added from left to right, which is important for
        node ordering in the returned data (so parents come before
        children).
        """
        node = node.parent
        path = []
        while node:
            # If a node has already been added, and _addParents is being
            # used, its parents must also already have been added, so we
            # break here instead of checking the rest of the parents.
            if node.oid in self.included_nodes:
#                print 'EARLY BREAK, parent check', node
                break
            path.insert(0, node)
            node = node.parent
        for node in path:
            self._addNodeAndAttributes(node)

    def _addNode(self, node):
        """Add a node and it's data to self.prepared_data."""
        if node.oid not in self.included_nodes:
            self.included_nodes[node.oid] = True
            self.prepared_data.append(entity_data_cache.getNodeData(node, self.user))

    def _addNodeAndAttributes(self, node):
#        """Add a node and all it's attributes to self.prepared_data."""
#        # If a node has already been added, so should all of it's attributes,
#        # so we should safely be able to abort early to save time.
#        if node.oid in self.included_nodes:
##            print 'EARLY BREAK, node added', node
#            return
        self._addNode(node)
        include = ['attribute', 'versioned attribute']
        for child in node.traverse(include_self = False, include = include,
                no_match_break = True, user = self.user):
            if child.oid not in self.included_nodes:
                self._addNode(child)

class NodeDataRegistry(object):
    """A registry for functions to collect data for node classes.

    Used to store mappings from class id's to functions that can collect
    data from objects matching the class and return it in a form suitable
    for returning to clients.
    """
    def __init__(self):
        self.object_classes = {}

    def register(self, class_reference, data_collector):
        """Register an object class and it's collector function."""
        self.object_classes[class_reference.class_id] = data_collector

    def extract(self, node, user):
        """Extract and return data from a node.

        Uses the function registered for the node class type with .register.
        """
        func = self.object_classes.get(node.class_id)
        if not func:
            raise Exception('no data extraction class available for %s' % (node.class_id))
        return self.object_classes[node.class_id](node, user)

    def exists(self, node):
        return node.class_id in self.object_classes

def no_data_extractor(node, user):
    """Dummy function that collects no data for the NodeDataRegistry."""
    return []

node_data_registry = NodeDataRegistry()
entity_data_cache = EntityDataCache(node_data_registry)

