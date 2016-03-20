import sys
from twisted.python import log, syslog, logfile
from siptrackdlib.errors import SiptrackError

class Logger(object):
    def __init__(self):
        self.setup_complete = False
        self.debug_logging = False

    def msg(self, message, user = None):
        if not self.setup_complete:
            return
        if user:
            username = user.user._username.get()
            message = '[%s] %s' % (username, message)
        if type(message) is unicode:
            message = message.encode('utf-8')
        log.msg(message)

    def debug(self, message, user = None):
        if not self.setup_complete or not self.debug_logging:
            return
        if user:
            username = user.user._username.get()
            message = '[%s] %s' % (username, message)
        if type(message) is unicode:
            message = message.encode('utf-8')
        log.msg(message)

    def setup(self, daemon, log_syslog, log_file, debug = False):
        observer = None
        if log_syslog:
            observer = syslog.SyslogObserver('siptrackd').emit
        elif log_file:
            if log_file == '-':
                if daemon:
                    raise SiptrackError('Daemons can\'t log to stdout')
                log_fd = sys.stdout
            else:
                log_fd = logfile.LogFile.fromFullPath(log_file)
            observer = log.FileLogObserver(log_fd).emit
        else:
            raise SiptrackError('No logging method selected')
        log.startLoggingWithObserver(observer)
        sys.stdout.flush()
        self.debug_logging = debug
        self.setup_complete = True
        return True

try:
    logger
except NameError:
    logger = Logger()
    msg = logger.msg
    debug = logger.debug
