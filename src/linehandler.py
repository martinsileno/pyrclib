import threading

class LineHandler(threading.Thread):
    def __init__(self, bot, socket):
        self._bot = bot
        self._socket = socket
        self._fo = self._socket.makefile('rb')
        threading.Thread.__init__(self)
        self._CRLF = '\r\n'
    
    def run(self):
        pass
