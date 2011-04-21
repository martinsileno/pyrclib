import threading

class LineHandler(threading.Thread):
    """Base class for LineReceiver and LineSender threads.
    """
    def __init__(self, bot, socket):
        self._bot = bot
        self._socket = socket
        self._fo = self._socket.makefile('rb')
        self._cond = threading.Condition()
        threading.Thread.__init__(self)
        self._CRLF = '\r\n'
    
    def run(self):
        pass
