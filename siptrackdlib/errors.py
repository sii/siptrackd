class SiptrackError(StandardError):
    """Generic siptrackd error."""
    pass

class InvalidStorageVersion(SiptrackError):
    pass

class StorageError(SiptrackError):
    """Generic siptrackd storage error."""
    pass

class AlreadyExists(SiptrackError):
    """Generic object already exists error."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'object already exists'
        return ret

class NonExistent(SiptrackError):
    """Generic object doesn't exist error."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'object doesn\'t exist'
        return ret

class NonExistentParent(NonExistent):
    """Parent object doesn't exist error."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'parent object doesn\'t exist'
        return ret

class PermissionDenied(NonExistent):
    """Permission denied."""
    def __str__(self):
        if len(self.args) == 1:
            ret = self.args[0]
        else:
            ret = 'permission denied'
        return ret

class InvalidNetworkAddress(SiptrackError):
    pass

