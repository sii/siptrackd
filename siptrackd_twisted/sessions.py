import hashlib
import random
import time
import errors
from twisted.internet import threads

# Two days.
DEFAULT_IDLE_TIMEOUT = 60 * 60 * 24 * 2
# Two days.
MAX_IDLE_TIMEOUT = 60 * 60 * 24 * 2

class DataIterators(object):
    def __init__(self):
        self.iterators = {}

    def add(self, iterator):
        i_id = self.getID(iterator)
        iter_data = {'iter': iterator}
        iter_data['data'], iter_data['has_data'] = self._getIterData(iterator)
        self.iterators[i_id] = iter_data
        return i_id

    def remove(self, iterator):
        i_id = self.getID(iterator)
        if i_id in self.iterators:
            del self.iterators[i_id]

    def getID(self, iterator):
        return str(id(iterator))

    def _getIterData(self, iterator):
        try:
            data = iterator.next()
            has_data = True
        except StopIteration:
            data = None
            has_data = False
        return data, has_data

    def _getNextData(self, iter_data):
        cur_data = iter_data['data']
        if iter_data['has_data']:
            iter_data['data'], iter_data['has_data'] = self._getIterData(iter_data['iter'])
        return cur_data, iter_data['has_data']

    def getData(self, i_id):
        if not i_id:
            return False
        iter_data = self.iterators.get(i_id)
        if not iter_data:
            return False
        ret = {'next': i_id}
        ret['data'], has_data = self._getNextData(iter_data)
        if not has_data:
            ret['next'] = False
            del self.iterators[i_id]
        return ret

    def threadGetData(self, i_id):
        return threads.deferToThread(self.getData, i_id)

class Session(object):
    def __init__(self, max_idle):
        shasum = hashlib.sha1()
        shasum.update(str(time.time()))
        shasum.update(str(random.getrandbits(128)))
        self.id = shasum.hexdigest()
        self.access_time = time.time()
        self.location = None
        self.user = None
        self.max_idle = max_idle
        self.data_iterators = DataIterators()

    def __str__(self):
        return self.id

    def __eq__(self, other):
        if self.id == other:
            return True
        return False

    def accessed(self):
        self.access_time = time.time()

    def idletime(self):
        return time.time() - self.access_time

    def setMaxIdle(self, timeout):
        if timeout > MAX_IDLE_TIMEOUT:
            raise errors.SiptrackError('session timeout value to large')
        self.max_idle = timeout

class SessionHandler(object):
    expire_interval = 600 # seconds
    def __init__(self, default_idle = DEFAULT_IDLE_TIMEOUT):
        self.default_idle = default_idle
        self.sessions = {}
        self.last_expire = 0

    def startSession(self):
        session = Session(self.default_idle)
        self.sessions[session.id] = session
        return session

    def endSession(self, session_id):
        if session_id not in self.sessions:
            raise errors.InvalidSessionError()
        del self.sessions[session_id]

    def fetchSession(self, session_id):
        self._expireSessions()
        if session_id not in self.sessions:
            raise errors.InvalidSessionError()
        return self.sessions[session_id]

    def _expireSessions(self):
        if not self._isTimeToExpire():
            return
        self.last_expire = time.time()
        expire = []
        for session_id in self.sessions:
            session = self.sessions[session_id]
            if session.idletime() > session.max_idle:
                expire.append(session_id)
            if not session.user or not session.user.user:
                expire.append(session_id)
            if session.user.user.removed:
                expire.append(session_id)
        for session_id in expire:
            del self.sessions[session_id]

    def _isTimeToExpire(self):
        now = time.time()
        diff = now - self.last_expire
        if diff > self.expire_interval:
            return True
        return False

    def killUserSessions(self, user):
        kill = []
        for session_id in self.sessions:
            session = self.sessions[session_id]
            # session.user is a UserInstance, we want the User
            if session.user.user == user:
                kill.append(session_id)
        for session_id in kill:
            del self.sessions[session_id]

    def killAllSessions(self):
        session_ids = [session_id for session_id in self.sessions]
        for session_id in session_ids:
            self.endSession(session_id)

