import re
import time

from siptrackdlib import errors
from siptrackdlib import storagevalue
from siptrackdlib import log
from siptrackdlib.objectregistry import object_registry

class PermissionCache(object):
    def __init__(self):
        self.cache = {}

    def clear(self):
        self.cache = {}

    def init(self, node):
        if node.oid not in self.cache:
            self.cache[node.oid] = []

    def add(self, node, perm):
        self.init(node)
        self.cache[node.oid].append(perm)

    def cached(self, node):
        return node.oid in self.cache

    def get(self, node):
        if node.oid in self.cache:
            return self.cache[node.oid]
        return []

perm_cache = PermissionCache()

def remove_callback(branch, user):
    """Branch callback used to remove a node.

    Called when a branch is removed in the object tree.
    """
    if branch.ext_data is not None:
        branch.ext_data._remove(user)

def load_data_callback(branch):
    """Branch callback used to load a node.

    Called when someone gets a branches ext_data and the node hasn't already
    been loaded.
    """
    ret = None
    if branch.oid in branch.tree.ext_data.oid_class_mapping:
        class_id = branch.tree.ext_data.oid_class_mapping[branch.oid]
        obj = object_registry._createObject(class_id, branch)
        if branch.tree.ext_data.call_loaded:
            obj._loaded(data = None)
        ret = obj
    return ret

def relocate_callback(branch):
    """Branch callback used when relocating a branch/node."""
    if branch.ext_data:
        branch.ext_data._relocate()

class NodeFilter(object):
    """A filter for object tree branch traversal.

    Can be used as a filter for traversal of branches (branch.traverse).
    include : a list of classes to be included, everything will be included
        if empty.
    exclude : a list of classes to exclude, has priority over the include
        list.
    no_match_break : will prevent further recursing down unmatches nodes.
    user : user to use for permission matching.
    """
    result_match = 1
    result_no_match = 0
    result_break = -1
    def __init__(self, include = [], exclude = [], no_match_break = False,
            user = None):
        self.include_all = False
        self.user = user
        if len(include) == 0:
            self.include_all = True
        self.ret_match = 1
        self.ret_no_match = 0
        if no_match_break:
            self.ret_no_match = -1
        self.result = 0
        if type(include) == list:
            self.include = {}
            for i in include:
                self.include[i] = True
        else:
            self.include = include
        if type(exclude) == list:
            self.exclude = {}
            for e in exclude:
                self.exclude[e] = True
        else:
            self.exclude = exclude

    def filter(self, branch):
        """Filter a branch through the filter rules.

        Returns -1 for no match + halt of further traversal down that
        branch. 0 for regular no match. 1 for match.
        """
        # Avoid removed nodes.
        if branch.ext_data.removed:
            self.result = self.result_break
        # If we have a user and it doesn't have proper permissions,
        # always leave the branch.
        elif self.user and not branch.ext_data.hasReadPermission(self.user):
            self.result = self.result_break
        # Matched exclude, don't yield.
        elif branch.ext_data.class_name in self.exclude:
            self.result = self.ret_no_match
        # Include list empty, include anything not excluded.
        elif self.include_all:
            self.result = self.ret_match
        # Matched include, yield.
        elif branch.ext_data.class_name in self.include:
            self.result = self.ret_match
        # We didn't match excludes, but not includes either, counts as no
        # match.
        else:
            self.result = self.ret_no_match
        return self.result

class BaseNode(object):
    """Base class for all objects in the tree.

    This class is inherited by all regular tree objects, views,
    containers etc.
    """
    require_admin = False

    def __init__(self, oid, branch):
        self.oid = oid
        self.branch = branch
        # Contains a list of all StorageValue instances used by the node.
        # Updated by StorageValue.__init__.
        self._storage_actions = []
        self.object_store = self.branch.tree.ext_data
        self.searcher = self.object_store.searcher
        self.removed = False
        # Creation time.
        self.ctime = storagevalue.StorageValue(self, 'ctime', 0)
        # Modification time, for internal use.
        self.modtime = time.time()
        global perm_cache
        self.perm_cache = perm_cache

    def __str__(self):
        return '<%s:%s>' % (self.class_name, self.oid)

    def _treeFree(self):
        """Free a BaseNode.

        This will free any memory references used by the node.
        The node will be unusable after this is called.

        Called by the object tree branch when it's freed.
        """
        self.oid = None
        self.branch = None
        self.object_store = None
        self.searcher = None
        self.perm_cache = None
        self._storage_actions = None

    def storageAction(self, action, args = None):
        self._storage_actions.append({'action': action, 'args': args})

    def addChildByID(self, user, class_id, *args, **kwargs):
        """Create a new child of type class_id.

        Checks the object registry that class_id is a valid child of
        the current object. Also creates a new branch in the object tree
        to hold the object.
        """
        if not object_registry.isValidChild(self.class_id, class_id):
            raise errors.SiptrackError(
                    'trying to create child of invalid type \'%s\'' % (class_id))
        if not self.hasWritePermission(user):
            raise errors.PermissionDenied()
        child = object_registry.createObject(class_id, self.branch,
                *args, **kwargs)
        try:
            # Called only for newly created objects.
            child._created(user)
        except Exception, e:
            child.remove(recursive = False)
            raise
        log.msg('Added node %s' % (child))
        self.branch.tree.ext_data.oid_class_mapping[child.oid] = class_id
        return child

    def addChildByName(self, user, class_name, *args, **kwargs):
        """Identical to addChildByID, but with class_name."""
        class_id = object_registry.getIDByName(class_name)
        if class_id is None:
            raise errors.SiptrackError(
                    'trying to create child of invalid type \'%s\'' % (class_name))
        return self.addChildByID(user, class_id, *args, **kwargs)
    add = addChildByName
    addChild = addChildByName

    def _created(self, user):
        """Called when an object has been newly created.

        As opposed to when an already existing object is just being loaded.
        May be overriden if work needs to be done here.
        """
        self.ctime.set(int(time.time()))
        self.object_store.triggerEvent('node add', self)
        self.storageAction('create_node')

    def _loaded(self, data = None):
        """Called when an existing object has just been loaded.

        As opposed to when an object has just been created for the first
        time (see: ._created()).
        Should be overriden if work needs to be done here.

        data _might_ contain a dict with a nodes storage data in the form:
        dict['data name'] = (data_type, data)
        This depends on how the node was loaded. Currently data is included
        if loading has happened via the ObjectStores preload method,
        otherwise not. Nodes should be able to deal with both having data
        passed in and loading it themselves from storage.
        May be overriden if work needs to be done here.
        """
        self.ctime.preload(data)

    def remove(self, recursive, user = None):
        """Remove an object.

        Callbacks from the objecttree branches being removed will call
        _remove for each object being removed.
        """
        return self.branch.remove(recursive, user)
    delete = remove

    def _remove(self, user):
        """Remove a single object. Called from branch callbacks."""
        if not self.hasWritePermission(user):
            raise errors.PermissionDenied()
        self.object_store.triggerEvent('node remove', self)
        log.msg('Removed node %s' % (self))
        for reference in list(self.references):
            reference.disassociate(self)
        for assoc in list(self.associations):
            self.disassociate(assoc)
        self.branch = None
        self.oid = None
        self.removed = True
        self.setModified()
        self.storageAction('remove_node')

    def _relocate(self):
        """Relocate (new parent) an object. Called from branch callbacks.
        
        Not for manual usage, should only be called by the branch callback
        when a branch is relocated.
        """
        self.storageAction('relocate')
        self.setModified()

    def relocate(self, new_parent, user = None):
        """Relocate (new parent) an object. Called manually.

        For manual use. Will relocate the objects branch and let the
        callback (_relocate) do the work.
        """
        if not self.hasWritePermission(user) or not new_parent.hasWritePermission(user):
            raise errors.PermissionDenied()
        # Don't set a node as its own parent..
        if self.oid == new_parent.oid:
            raise errors.SiptrackError('I really can\'t be my own parent..')
        # Make sure the new parent class can have us as a child.
        if not object_registry.isValidChild(new_parent.class_id, self.class_id):
            raise errors.SiptrackError('incompatible classes for relocation')
        # Make sure we aren't moving between views.
        if self.getParent('view') is not new_parent.getParent('view'):
            raise errors.SiptrackError('can\'t relocate between views')
        # Make sure we aren't trying to relocate to one of our children.
        node = new_parent
        while node:
            if node is self:
                raise errors.SiptrackError('can\'t relocate to a child')
            node = node.parent
        self.branch.relocate(new_parent.branch)
        self.object_store.triggerEvent('node relocate', self)
        self.setModified()

    def prune(self, user = None):
        """Used to prune empty/unused nodes.
        
        Override me in a subclass.
        See for example network.ipv4.Network for sample usage.
        """
        return

    def associate(self, other):
        """Associate an object with another object.

        This creates a link between two objects. The associated object
        will also keep a reference to this object.
        Associations/references are stored in the object tree as
        associations between branches.
        """
        if self.isAssociated(other):
            raise errors.SiptrackError('objects already associated')
        if self is other:
            raise errors.SiptrackError('can\'t associate an object with itself')
        self.storageAction('associate', {'other': other.oid})
        self.branch.associate(other.branch)
        self.object_store.triggerEvent('node associate', self, other)
        self.setModified()
        other.setModified()

    def disassociate(self, other):
        """Remove an association to another object."""
        if not self.isAssociated(other):
            raise errors.SiptrackError('objects not associated')
        self.storageAction('disassociate', {'other': other.oid})
        self.branch.disassociate(other.branch)
        self.object_store.triggerEvent('node disassociate', self, other)
        self.setModified()
        other.setModified()

    def isAssociated(self, other):
        # Just check the tree to avoid loading nodes unnecessarily.
        for branch in self.branch.associations:
            if other.oid == branch.oid:
                return True
        return False

    def listAssocRef(self, include = [], exclude = []):
        """List associations and references.

        If one or more class names are given in 'include' only nodes
        of those types will be included.
        """

        for node in (list(self.associations) + list(self.references)):
            if include:
                if node.class_name not in include:
                    continue
            if node.class_name in exclude:
                continue
            yield node

    def disAssocRef(self, other):
        """Remove an association or reference."""
        if self.isAssociated(other):
            self.disassociate(other)
        elif other.isAssociated(self):
            other.disassociate(self)
        else:
            raise errors.SiptrackError('objects not associated')

    def _get_associations(self):
        """Iterate branch associations, returning nodes, not branches."""
        for branch in self.branch.associations:
            yield branch.ext_data

    def _set_associations(self, value):
        return
    associations = property(_get_associations, _set_associations)

    def _get_references(self):
        """Iterate branch references, returning nodes, not branches."""
        for branch in self.branch.references:
            yield branch.ext_data

    def _set_references(self, value):
        return
    references = property(_get_references, _set_references)

    def traverse(self, include_self = True, max_depth = -1,
            include = [], exclude = [], no_match_break = False,
            include_depth = False, user = None):
        """Tree traversal.

        Just like branch.traverse but returns nodes, not branches.
        include/exclude are used to filter results with the NodeFilter
        class.
        """
        node_filter = NodeFilter(include, exclude, no_match_break, user)
        for data in self.branch.traverse(include_self, max_depth, node_filter,
                include_depth):
            if include_depth:
                # depth, branch
                yield data[0], data[1].ext_data
            else:
                # branch
                yield data.ext_data

    def listChildren(self, include = [], exclude = []):
        """List directly attached children.

        A depth 0, no include self wrapper for traverse.
        """
        return self.traverse(include_self = False, max_depth = 0,
                include = include, exclude = exclude)

    def search(self, re_pattern, attr_limit = [], include = [], exclude = [],
            no_match_break = False, user = None):
        re_compiled = re.compile(re_pattern, re.IGNORECASE)
        """Searches for nodes.
        
        Search the node tree for nodes attributes that match the regular
        expression re_pattern.

        re_pattern : a regular expression that is matched again attribute
            values
        attr_limit : limits the search to attributes with names in the given
            list
        include    : include only node types listed
        exclude    : exclude node types listed
        no_match_break : see argument with same name to traverse
        """
        match_any_attrs = True
        if len(attr_limit) > 0:
            match_any_attrs = False
        local_include = ['attribute', 'versioned attribute', 'ipv4 network', 'ipv6 network']
        prev_added = None
        node_filter = NodeFilter(include, exclude, no_match_break)
#        for node in self.traverse(include = local_include, exclude = exclude,
#                no_match_break = no_match_break, user = user):
        # Don't include the user in the traverse. If we did we wouldn't be
        # able to match nodes further into the tree that we do have
        # access to. We do permission checking ourselves below.
        for node in self.traverse(include = local_include, exclude = exclude,
                no_match_break = no_match_break, user = None):
            if not node.hasReadPermission(user):
                continue
            # Match attributes.
            if node.class_name in ['attribute', 'versioned attribute']:
                value = node.value
                if node.atype in ['int', 'bool']:
                    value = str(value)
                if (match_any_attrs or node.name in attr_limit) and \
                        node.atype in ['text', 'int', 'bool'] and \
                        re_compiled.search(value):
                    # Get the attributes nearest _non-attribute_ parent.
                    parent = node.getParentNode()
                    if parent is not prev_added and \
                            node_filter.filter(parent.branch) == \
                            node_filter.result_match and \
                            parent.hasReadPermission(user):
                        yield parent
                        prev_added = parent
            # Match networks.
            elif node.class_name in ['ipv4 network', 'ipv6 network']:
                if re_compiled.search(str(node.address)) and \
                        node is not prev_added and \
                        node_filter.filter(node.branch) == \
                        node_filter.result_match:
                    yield node
                    prev_added = node

    def getParent(self, class_name):
        """Return the nearest matching parent of type class_name.
        
        This is sort of ugly.
        """
        match = self.parent
        while match:
            if match.class_name == class_name:
                return match
            match = match.parent
        return None

    def _get_parent(self):
        """Returns the nodes parent."""
        # Sort of ugly.. but, view trees have no parents.
        if self.class_id == 'VT':
            return None
        return self.branch.parent.ext_data

    def _set_parent(self, value):
        return
    parent = property(_get_parent, _set_parent)

    def iterParents(self, include_self = False):
        if include_self:
            parent = self
        else:
            parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    def getAttribute(self, name):
        """Returns the first matched directly attached attribute with name.
        
        This is a bit of an ugly hack. Should be cleaned up.
        """
        for obj in self.listChildren(
                include = ['attribute', 'versioned attribute']):
            if obj.name == name:
                return obj
        return None

    def getAttributeValue(self, name, default = None):
        attr = self.getAttribute(name)
        if not attr:
            return default
        return attr.value

    def getPermission(self, user, recurse = True):
        self._cachePermissions()
        for perm in self.perm_cache.get(self):
            if perm.matchesUser(user):
                return perm

    def _cachePermissions(self):
        if self.perm_cache.cached(self):
            return
        self.perm_cache.init(self)
        # First add our own permission children.
        for perm in self.listChildren(include = ['permission']):
            self.perm_cache.add(self, perm)
        parent = self.parent
        if parent:
            # If we have a parent, tell it to cache it's permissions.
            parent._cachePermissions()
            # Next, add the parents recursive permissions to our own
            # perm cache.
            for perm in self.perm_cache.get(parent):
                if perm.recursive.get():
                    self.perm_cache.add(self, perm)

    def logPermissionCache(self, user = None):
        for perm in self.perm_cache.get(self):
            log.msg(str(perm))
            if user and perm.matchesUser(user):
                log.msg('matches user %s: true' % (user))

    def hasReadPermission(self, user, recurse = True):
        if not user or user.administrator:
            return True
        if self.require_admin and not user.administrator:
            return False
        # Users have access to their own users.
        if self == user.user:
            return True
        perm = self.getPermission(user, recurse)
        if perm and perm.read_access.get():
            return True
        log.msg('FAIL: read permission failed for node:%s user:%s, permitting anyway' % (self, user))
        return True
#        return False

    def hasWritePermission(self, user, recurse = True):
        if not user or user.administrator:
            return True
        if self.require_admin and not user.administrator:
            return False
        # Users have access to their own users.
        if self == user.user:
            return True
        perm = self.getPermission(user, recurse)
        if perm and perm.write_access.get():
            return True
        log.msg('FAIL: write permission failed for node:%s user:%s, permitting anyway' % (self, user))
        return True
#        return False

    def buildSearchValues(self):
        values = {}
        for attribute in self.listChildren(include = ['attribute', 'versioned attribute']):
            attr_values = attribute.buildSearchValues()
            values.update(attr_values)
        values['nodeclass'] = values['nodetype'] = values['type']= unicode(self.class_name)
        return values

    def setModified(self):
        self.modtime = time.time()
