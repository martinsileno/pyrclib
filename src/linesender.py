import time
from collections import deque
from linehandler import LineHandler

class LineSender(LineHandler):
    """This thread handles outgoing messages. 
    It will sleep until a new element is added to the queue and then wake up
    to send it.
    It adds a configurable delay between each line sent, to avoid getting
    disconnected from the server for excess flood.
    """
    
    def __init__(self, bot, socket, delay):
        LineHandler.__init__(self, bot, socket)
        self.delay = delay
        self.queue = deque()
    
    def raw_line(self, line):
        self._socket.sendall((line + self._CRLF).encode())
        self._bot.logger.log('>>> ' + line)
        
    def run(self):
        while(True):
            msg = self.pop()
            if msg:
                self.raw_line(msg)
                time.sleep(self.delay / 1000)
            else:
                self._cond.acquire()
                self._cond.wait()
                self._cond.release()
    
    def add(self, msg):
        self._cond.acquire()
        self.queue.append(msg)
        self._cond.notify()
        self._cond.release()
    
    def is_empty(self):
        if self.queue:
            return False
        else:
            return True
    
    def pop(self):
        if self.queue:
            msg = self.queue.popleft()
        else:
            msg = None
        
        return msg
    
    def set_delay(self, new_delay):
        """Change delay between each message sent to the server.
        """
        self.delay = new_delay
