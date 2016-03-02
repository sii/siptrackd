import sys
import time

from siptrackdlib import errors
from siptrackdlib import log

class FilterInclude(object):
    """A traversal filter that always returns 1 (matched)."""
    def __init__(self):
        self.result = 1

    def filter(self, branch):
        return 1
filter_include = FilterInclude()

def traverse_tree_depth_first(root, include_root, max_depth, filter = None,
        include_depth = False):
    """Depth-first iteration through a tree starting at 'root'.

    If include_root is true also returns the root object given, otherwise
    only children will be returned.
    Only max_depth branches will be traversed, setting max_depth to -1 will
    skip depth checking.
    If include_depth is included the current depth is yielded along with
    the branch.

    Filters can be used to filter the results, if a filter is passed in
    it must have a filter method that accepts a branch and returns one
    of the following:
    -1 : exclude branch and it's children.
     0 : exclude branch but not it's children.
     1 : include branch.
    Filters must also have a result attribute that contains the result
    of the last filter operation.
    """
    if filter == None:
        filter = filter_include
    depth = 0
    if include_root:
        if filter.filter(root) == -1:
            return
        if filter.result == 1:
            if include_depth:
                yield (depth, root)
            else:
                yield root
        depth += 1
    # We only yield the branch itself if max_depth = 0 and
    # include_self = True.
    if max_depth != -1 and depth > max_depth:
        return
    iterators = []
    cur_iterator = iter(root.branches)
    while cur_iterator != None:
        try:
            branch = cur_iterator.next()
            if filter.filter(branch) == 1:
                if include_depth:
                    yield (depth, branch)
                else:
                    yield branch
            if branch.branches and filter.result != -1 and \
                    (max_depth == -1 or depth < max_depth):
                depth += 1
                iterators.append(cur_iterator)
                cur_iterator = iter(branch.branches)
        except StopIteration:
            if len(iterators) > 0:
                cur_iterator = iterators.pop()
                depth -= 1
            else:
                cur_iterator = None

def traverse_tree_reverse(root, include_root):
    """Reverse depth-first iteration through a tree starting at 'root'.

    Iterate through a tree in reverse order, the outermost branches
    will be returned first.
    If include_root is true also returns (last) the root object given,
    otherwise only children will be returned.
    """
    iterators = []
    cur_iterator = iter(root.branches)
    while cur_iterator != None:
        try:
            branch = cur_iterator.next()
            if branch.branches:
                iterators.append((cur_iterator, branch))
                cur_iterator = iter(branch.branches)
            else:
                yield branch
        except StopIteration:
            if len(iterators) > 0:
                cur_iterator, branch = iterators.pop()
                yield branch
            else:
                cur_iterator = None
    if include_root:
        yield root

class Branch(object):
    """A single branch in a tree.

    A branch is a node in a tree. A branch can also have its own branches
    (sub-nodes). Each branch is identified globally by an object id (oid)
    that is stored for easy lookup in the tree.
    """
    def __init__(self, tree, parent, oid, ext_data = None):
        """Init.

        tree is the.. tree.
        parent is the parent branch.
        oid is the branches object id.
        ext_data is any external data to be stored.
        """
        self.tree = tree
        self.parent = parent
        self.oid = oid
        self.branches = []
        self.associations = []
        self.references = []
        self._ext_data = ext_data

    def __iter__(self):
        for branch in traverse_tree_depth_first(self, include_root = True):
            yield branch

    def __str__(self):
        return '<objecttree.Branch oid = %s>' % (self.oid)

    def free(self):
        """Free a branch.

        Release all memory references the branch has.
        The branch will be unusable after this.
        """
        self.tree = None
        self.parent = None
        self.selfes = None
        self.associations = None
        self.references = None
        if self._ext_data and hasattr(self._ext_data, '_treeFree'):
            self._ext_data._treeFree()
        self._ext_data = None

    def _removeRecursive(self, callback_data):
        affected_extdata = []
        for branch in list(traverse_tree_reverse(self, include_root = True)):
            affected_extdata += branch._removeSingle(callback_data)
        return affected_extdata

    def _removeSingle(self, callback_data):
        """Removes a single branch from the tree.

        Child branches will be moved to the parent branch.
        """
        affected_extdata = [self.ext_data]
        self.tree.remove_callback(self, callback_data)
        self.tree.removedBranch(self.oid)
        branches = list(self.branches)
        for branch in branches:
            branch.relocate(self.parent)
            affected_extdata.append(branch.ext_data)
        self.branches = None
        self.parent.branches.remove(self)
        self.parent = None

        for association in list(self.associations):
            self.disassociate(association)
        self.associations = None
        for reference in list(self.references):
            reference.disassociate(self)
        self.references = None

        self.tree = None
        self.oid = None
        self.ext_data = None
        return affected_extdata

    def remove(self, recursive, callback_data):
        """Remove a branch.

        If recursive is true, all child branches will also be removed,
        otherwise they will be moved to the parent branch.
        """
        if recursive:
            ret = self._removeRecursive(callback_data)
        else:
            ret = self._removeSingle(callback_data)
        return ret

    def relocate(self, new_parent):
        """Relocate a branch (give it a new parent)."""
        self.parent.branches.remove(self)
        new_parent.branches.append(self)
        self.parent = new_parent
        self.tree.relocate_callback(self)

    def addBranch(self, oid, ext_data = None):
        """Create a new directly attached branch."""
        if self.tree.branchExists(oid):
            raise errors.SiptrackError(
                    'a branch with oid %s already exists' % (oid))
        branch = Branch(self.tree, self, oid, ext_data)
        self.branches.append(branch)
        self.tree.addedBranch(oid, branch)
        return branch
    add = addBranch

    def associate(self, other):
        """Associate a branch with another branch.

        This creates a link between two branches. The associated branch
        will also keep a reference to this branch.
        """
        if other:
            self.associations.append(other)
            other.reference(self)

    def reference(self, other):
        """Create a reference to another branch.

        This is the inverse of an association.
        """
        if other:
            self.references.append(other)

    def disassociate(self, other):
        """Remove an association to another branch."""
        self.associations.remove(other)
        other.dereference(self)

    def dereference(self, other):
        """Remove a reference to another branch."""
        self.references.remove(other)

    def traverse(self, include_self, max_depth, filter = None,
            include_depth = False):
        """Depth-first traversal of the branch and it's children.

        If include_self is True yield the current branch first.
        """
        return traverse_tree_depth_first(self, include_self, max_depth,
                filter, include_depth)

    def hasExtData(self):
        """Check if self._ext_data exists (isn't None)."""
        if self._ext_data is None:
            return False
        return True

    def _get_ext_data(self):
        """Return a branches external data.

        If no external data is available try to load it from the tree.
        """
        if self._ext_data is None:
            self._ext_data = self.tree.load_data_callback(self)
        return self._ext_data

    def _set_ext_data(self, value):
        """Set a branches external data."""
        self._ext_data = value
    ext_data = property(_get_ext_data, _set_ext_data)

class Tree(object):
    """A hierarchal tree containing branches.

    A tree consists of a hierarchal structure of branches/sub-branches.
    Each branch is identified by a unique object id (oid) for easy direct
    lookup/access.
    """
    def __init__(self, callbacks = {}, ext_data = None):
        """Init.

        self.branches contains the directly attached branches.
        self.oid_mapping is a mapping of oids to branches.

        callbacks is a dictionary that can contain the following
        keys:
            'load_data': called to load external data for a branch
            'remove'   : called if a branch is being removed
        The key should point to a function that takes a branch as an argument.

        ext_data can contain, anything, for access by branches ext_data
        objects.
        """
        self.branches = []
        self.oid_mapping = {}
        self.callbacks = callbacks
        self.ext_data = ext_data

    def __iter__(self):
        for branch in traverse_tree_depth_first(self, include_root = False):
            yield branch

    def __str__(self):
        return '<objecttree.Tree>'

    def branchExists(self, oid):
        """Check if a branch with the given oid exists in the tree."""
        if oid in self.oid_mapping:
            return True
        return False

    def getBranch(self, oid):
        """Fetch a branch by its object id.
        
        Returns None if no branch with that oid exists.
        """
        if oid in self.oid_mapping:
            return self.oid_mapping[oid]
        return None

    def addedBranch(self, oid, branch):
        """Notification of new branch creation.

        Used to notify the tree of a new branch being created somewhere in
        the tree.
        """
        self.oid_mapping[oid] = branch

    def removedBranch(self, oid):
        """Notification of branch removal.

        Used to notify the tree of a branch being removed somewhere in the
        tree.
        """
        del self.oid_mapping[oid]

    def addBranch(self, oid, ext_data = None):
        """Create a new directly attached branch."""
        if self.branchExists(oid):
            raise errors.SiptrackError(
                    'a branch with oid %s already exists' % (oid))
        branch = Branch(self, self, oid, ext_data)
        self.branches.append(branch)
        self.addedBranch(oid, branch)
        return branch
    add = addBranch

    def traverse(self, max_depth = -1, filter = None, include_depth = False):
        """Depth-first traversal of the tree and it's branches."""
        return traverse_tree_depth_first(self, include_root = False,
                max_depth = max_depth, filter = filter,
                include_depth = include_depth)

    def loadBranches(self, branches):
        """Bulk addition of branches.

        'branches' is a list of (parent_oid, oid) pairs that will be
        added to the tree. If parent_oid is 'ROOT' the tree will be used as
        parent.
        """
        start = time.time()
        created_branches = []
        for parent_oid, oid in branches:
            if self.branchExists(oid):
                raise errors.SiptrackError(
                    'a branch with oid %s already exists' % (oid))
            branch = Branch(self, parent_oid, oid)
            self.addedBranch(oid, branch)
            created_branches.append(branch)
        for branch in self.oid_mapping.itervalues():
            if type(branch.parent) in [str, unicode]:
                if branch.parent == 'ROOT':
                    parent = self
                else:
                    parent = self.oid_mapping.get(branch.parent)
                if not parent:
                    log.msg('WARNING: unable to locate parent %s for oid %s' % (branch.parent, branch.oid))
#                    raise errors.SiptrackError(
#                        'unable to locate parent %s for oid %s' % (branch.parent, branch.oid))
                else:
                    branch.parent = parent
                    parent.branches.append(branch)

    def loadAssociations(self, associations):
        """Bulk addition of associations.

        'associations' is a list of (oid, associated_oid)
        pairs.
        """
        for oid, associated_oid in associations:
            branch = self.getBranch(oid)
            if not branch:
                log.msg('WARNING: unable to find oid %s (-> %s) when loading associations' % (oid, associated_oid))
                continue
            associated_branch = self.getBranch(associated_oid)
            if not associated_branch:
                log.msg('WARNING: unable to find associated oid %s (-> %s) when loading associations' % (associated_oid, oid))
                continue
            branch.associate(associated_branch)

    def load_data_callback(self, branch):
        """Fetch a branches external data using the 'load_data' callback.

        If the callback is unspecified None is returned.
        """
        if 'load_data' in self.callbacks:
            ret = self.callbacks['load_data'](branch)
            return ret
        return None

    def remove_callback(self, branch, callback_data):
        """Callback to indicate a branch being removed."""
        if 'remove' in self.callbacks:
            return self.callbacks['remove'](branch, callback_data)
        return None

    def relocate_callback(self, branch):
        """Callback to indicate a branch being relocated (new parent)."""
        if 'relocate' in self.callbacks:
            return self.callbacks['relocate'](branch)
        return None

    def free(self):
        """Free the object tree.

        This gets rid of the entire tree, releasing the branches etc.
        This is used to free up trees memory when it's use is finished.
        """
        for branch in traverse_tree_reverse(self, False):
            branch.free()
        self.branches = None
        self.oid_mapping = None
        self.callbacks = None
        self.ext_data = None
