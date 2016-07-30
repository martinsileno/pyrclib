import threading


class LineHandler(threading.Thread):
    """Base class for LineReceiver and LineSender threads.
    """

    def __init__(self, bot, fo):
        self._bot = bot
        self._fo = fo
        self._cond = threading.Condition()
        threading.Thread.__init__(self)
        self._CRLF = '\r\n'

    def run(self):
        pass
