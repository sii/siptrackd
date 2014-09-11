from siptrackdlib import errors

class ObjectClass(object):
    """A class definition in the object registry.

    Stores a reference to the class itself and also a list of valid child
    classes (class_ids).
    """
    def __init__(self, class_reference):
        self.class_reference = class_reference
        self.valid_children = {}

    def registerChild(self, class_reference):
        """Register a class as a valid child class."""
        self.valid_children[class_reference.class_id] = None

class ObjectRegistry(object):
    """Keeps track of registered classes and their valid children.

    The object registry is used to keep track of valid classes and
    what classes are valid children of a class.
    It also allocates object ids and can be used to create new objects
    based on the registry.
    """
    def __init__(self):
        self.object_classes = {}
        self.object_classes_by_name = {}
        self.next_oid = 0

    def registerClass(self, class_reference):
        """Register a new class.

        This creates a new ObjectClass and stores it in the registry,
        enabling creation of objects of the given class.
        The returned ObjectClass object can be used to register valid
        children of the class.
        """
        object_class = ObjectClass(class_reference)
        self.object_classes[class_reference.class_id] = \
                object_class
        self.object_classes_by_name[class_reference.class_name] = \
                object_class
        return object_class

    def isValidChild(self, parent_id, child_id):
        """Check if a class is a valid child of another class."""
        if not parent_id in self.object_classes:
            return False
        parent = self.object_classes[parent_id]
        if child_id not in parent.valid_children:
            return False
        return True

    def getClass(self, class_name):
        """Returns the class reference for class registered with class_name."""
        if class_name in self.object_classes_by_name:
            return self.object_classes_by_name[class_name].class_reference
        return None

    def getClassById(self, class_id):
        """Returns the class reference for class registered with class_name."""
        if class_id in self.object_classes:
            return self.object_classes[class_id].class_reference
        return None

    def getIDByName(self, class_name):
        """Return a classes id given it's name."""
        if class_name in self.object_classes_by_name:
            object_class = self.object_classes_by_name[class_name]
            return object_class.class_reference.class_id
        return None

    def allocateOID(self):
        """Allocate a new oid."""
        ret = str(self.next_oid)
        self.next_oid += 1
        return ret

    def revertOID(self):
        """Revert an oid allocation."""
        self.next_oid -= 1

    def createObject(self, class_id, parent_branch, *args, **kwargs):
        """Try to create a new object based on a registered class.

        This will try to create a new object of 'class_id' type, allocating
        it it's own oid. A new branch will also be created in the object
        tree to hold the object.
        """
        if class_id not in self.object_classes:
            raise errors.SiptrackError(
                    'trying to create object with invalid class id \'%s\'' % (class_id))
        object_class = self.object_classes[class_id]
        oid = self.allocateOID()
        branch = parent_branch.add(oid)
        try:
            obj = object_class.class_reference(oid, branch, *args, **kwargs)
        except:
            branch.remove(recursive = False, callback_data = None)
            self.revertOID()
            raise
        branch.ext_data = obj
        return obj

    def _createObject(self, class_id, branch):
        """Try to create _only_ a new object based on an oid and class id.

        Similar to createObject, but takes a class id and an oid and only
        creates a new object, no branch etc.
        """
        if class_id not in self.object_classes:
            raise errors.SiptrackError(
                    'trying to create object with invalid class id \'%s\'' % (class_id))
        object_class = self.object_classes[class_id]
        obj = object_class.class_reference(branch.oid, branch)
        return obj

object_registry = ObjectRegistry()
