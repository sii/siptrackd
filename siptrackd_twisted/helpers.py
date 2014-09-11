import time
import traceback

from twisted.internet import defer

import siptrackdlib.errors
from siptrackd_twisted import errors
from siptrackd_twisted import log

def ascii_to_unicode(string):
    """Convert a string to unicode.
    
    Since strings from xmlrpclib can be either unicode or ascii we need to
    convert them to unicode. If the string is already unicode, leave it alone.
    """
    if type(string) == str:
        return string.decode('ascii')
    return string

def error_handler(func):
    """Deal with SiptrackError and it's relatives.
    
    This is just a simple error handling wrapper for the exported xmlrpc
    methods. It handles SiptrackError and related errors in a graceful way.
    There's really nothing wrong with an exception ending up here.
    """
    def handle_errors(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
            if isinstance(ret, defer.Deferred):
                ret.addErrback(_eb_ret)
            return ret
        except Exception, e:
            return _check_exception(e)
    return handle_errors

def _eb_ret(error):
    print 'EEEEEEEEEEE', error
    return _check_exception(error.value)

def _check_exception(exc):
    if isinstance(exc, siptrackdlib.errors.AlreadyExists):
        return errors.client_error_exists(exc.__str__())
    elif isinstance(exc, errors.InvalidSessionError):
        return errors.invalid_session_error()
    elif isinstance(exc, errors.InvalidLocationError):
        return errors.client_error_invalid_location(exc.__str__())
    elif isinstance(exc, errors.InvalidLoginError):
        return errors.client_error_login(exc.__str__())
    elif isinstance(exc, errors.PermissionDenied):
        return errors.permission_denied(exc.__str__())
    elif isinstance(exc, siptrackdlib.errors.PermissionDenied):
        return errors.permission_denied(exc.__str__())
    elif isinstance(exc, siptrackdlib.errors.NonExistent):
        return errors.client_error_nexists(exc.__str__())
    elif isinstance(exc, siptrackdlib.errors.SiptrackError):
        tbmsg = traceback.format_exc()
        log.msg(tbmsg)
        return errors.generic_error(exc.__str__())
    else:
        tbmsg = traceback.format_exc()
        log.msg(tbmsg)
        return errors.generic_error(exc.__str__())

def validate_session(func):
    """Session validation.

    Wrapper to validate session id's for xmlrpc methods that require them
    The session id must be the first argument to the method (apart from self).
    The session itself (if validation occurs) is stored in self.session for
    the duration of the method call.
    """
    def validate(*args, **kwargs):
        if len(args) < 2:
            raise errors.InvalidSessionError()
        func_self = args[0]
        session_id = args[1]
        try:
            func_self.session = func_self.session_handler.fetchSession(session_id)
            func_self.session.accessed()
            log.logger.session = func_self.session
            args = (args[0],) + args[2:]
            func_self.tree_user = func_self.session.user.user
            func_self.instance_user = func_self.session.user
            func_self.user = func_self.instance_user
#            print func, args[1:], kwargs
            start = time.time()
            ret = func(*args, **kwargs)
#            print 'ELAPSED:', func, time.time() - start
            return ret
        finally:
            func_self.session = None
            log.logger.session = None
            func_self.tree_user = None
            func_self.instance_user = None
            func_self.user = None
    return validate

def require_admin(func):
    """Require administrator privileges."""
    def validate(*args, **kwargs):
        if len(args) < 1:
            raise errors.PermissionDenied()
        func_self = args[0]
        if not hasattr(func_self, 'session'):
            raise errors.PermissionDenied()
        session = func_self.session
        if not session.user or not session.user.user or not \
                session.user.user.administrator:
            raise errors.PermissionDenied()
        return func(*args, **kwargs)
    return validate
require_administrator = require_admin

