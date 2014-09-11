import xmlrpclib
from siptrackdlib.errors import SiptrackError

def generic_error(msg):
    """A generic xmlrpc error."""
    return xmlrpclib.Fault(1, msg)


def invalid_session_error():
    """Client sent an invalid session_id."""
    return xmlrpclib.Fault(99, 'invalid session id')


# Client errors start from 100.
def client_error(msg):
    """A generic xmlrpc client error."""
    return xmlrpclib.Fault(101, msg)

def client_error_exists(msg):
    """An 'object already exists' xmlrpc error for a client."""
    return xmlrpclib.Fault(102, msg)

def client_error_nexists(msg):
    """An 'object doesn't exist' xmlrpc error for a client."""
    return xmlrpclib.Fault(103, msg)

def client_error_invalid_location(msg):
    """Invalid location supplied by client."""
    return xmlrpclib.Fault(104, msg)

def client_error_login(msg):
    """Invalid username/password."""
    return xmlrpclib.Fault(105, msg)

def permission_denied(msg):
    """Permission denied."""
    return xmlrpclib.Fault(106, msg)

class InvalidLoginError(SiptrackError):
    """Invalid username/password."""
    def __str__(self):
        if len(self.args) == 1:
            ret = 'invalid login: %s' % (self.args[0])
        else:
            ret = 'invalid login'
        return ret

class InvalidSessionError(SiptrackError):
    """Invalid session id."""
    def __str__(self):
        if len(self.args) == 1:
            ret = 'invalid session id: %s' % (self.args[0])
        else:
            ret = 'invalid session id'
        return ret

class InvalidLocationError(SiptrackError):
    """Invalid object path supplied to server."""
    def __str__(self):
        if len(self.args) == 1:
            ret = 'invalid object path given: %s' % (self.args[0])
        else:
            ret = 'invalid object path given'
        return ret

class PermissionDenied(SiptrackError):
    """Permission denied."""
    def __str__(self):
        ret = 'permission denied'
        return ret
