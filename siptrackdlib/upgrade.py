from twisted.internet import defer

from siptrackdlib import errors

@defer.inlineCallbacks
def perform_upgrade(storage):
    ret = yield storage.upgrade()
    defer.returnValue(ret)

