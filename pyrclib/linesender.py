import logging
import time
from collections import deque
from pyrclib.linehandler import LineHandler

logger = logging.getLogger(__name__)


class LineSender(LineHandler):
    """This thread handles outgoing messages.
    It will sleep until a new element is added to the queue and then wake up
    to send it.
    It adds a configurable delay between each line sent, to avoid getting
    disconnected from the server for excess flood.
    """

    def __init__(self, bot, socket, fo, delay):
        LineHandler.__init__(self, bot, fo)
        self._socket = socket
        self.delay = delay
        self.queue = deque()
        self.alive = True

    def raw_line(self, line):
        self._socket.sendall((line + self._CRLF).encode())
        logger.info('>>> %s', line)

    def run(self):
        while self.alive:
            msg = self.pop()
            if msg:
                self.raw_line(msg)
                time.sleep(self.delay / 1000)
            else:
                with self._cond:
                    self._cond.wait()

    def add(self, msg):
        with self._cond:
            self.queue.append(msg)
            self._cond.notify()

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

    def stop(self):
        with self._cond:
            self.alive = False
            self._cond.notify()
