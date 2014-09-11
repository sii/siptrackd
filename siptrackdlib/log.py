class NoneLogger(object):
    def __init__(self):
        pass

    def msg(self, message):
        pass

def set_logger(l):
    global logger
    global msg
    logger = l
    msg = l.msg

try:
    logger
except NameError:
    logger = NoneLogger()
    msg = logger.msg
