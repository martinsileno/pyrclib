import time
from collections import deque
from linehandler import LineHandler

class LineSender(LineHandler):
    def __init__(self, bot, socket):
        LineHandler.__init__(self, bot, socket)
    
    def raw_line(self, line):
        self._socket.sendall((line + self._CRLF).encode())
        self._bot.logger.log('>>> ' + line)
        
    def run(self):
        while(True):
            msg = self._bot.msgqueue.pop()
            if msg:
                self.raw_line(msg)
            
            time.sleep(self._bot.msgqueue.delay / 1000)
    
class MessageQueue(object):
    def __init__(self, delay):
        self.delay = delay
        self.queue = deque()
    
    def add(self, msg):
        self.queue.append(msg)
    
    def pop(self):
        if len(self.queue) > 0:
            msg = self.queue.popleft()
        else:
            msg = None
        
        return msg
    
    def set_delay(self, new_delay):
        self.delay = new_delay