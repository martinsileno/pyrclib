import logging
import socket

from pyrclib.linereceiver import LineReceiver
from pyrclib.linesender import LineSender

logger = logging.getLogger(__name__)


class IRCConnection(object):
    """Represent a low level connectiont to an IRC server.
    """

    def __init__(self, nick, user, realname):
        self.nick = nick
        self.user = user
        self.realname = realname
        self.delay = 0
        self.is_connected = False
        self.server = None
        self.receiver = None
        self.sender = None

    def connect(self, address, port=6667, password=None, useSSL=False):
        """Connect to the specified IRC server.
        - address: the address of the server
        - port: port of the server, defaults to 6667
        - password: if a password is required to connect
        - useSSL: use a secure connection with SSL
        """
        self.server = address
        if self.is_connected:
            logger.error('Trying to connect to %s:%s while already connected'
                         'to %s', address, port, self.server)
            raise AlreadyConnectedException()

        logger.info('Connecting to server %s:%s', address, port)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((address, port))  # TODO: Exceptions?
        logger.debug('Socket initialized and connected')

        if useSSL:
            try:
                import ssl
            except ImportError:
                logger.exception('SSL not available')
                raise SSLNotAvailableException()
            s = ssl.wrap_socket(s)

        fo = s.makefile('rb')
        self.receiver = LineReceiver(self, fo)
        logger.debug('Initialized line receiver')

        # Manually handle connection to the server
        self.sender = LineSender(self, s, fo, self.delay)
        logger.debug('Initialized line sender')

        if password:
            self.sender.raw_line('PASS {0}'.format(password))

        self.sender.raw_line('NICK {0}'.format(self.nick))
        self.sender.raw_line(
            'USER {0} * * :{1}'.format(self.user, self.realname))

        while True:
            line = fo.readline()
            if not line:
                break

            line = line.decode()
            if line[-2:] == '\r\n':
                line = line[:-2]

            logger.info('<<< %s', line)
            if line.startswith('PING') or line.startswith('PONG'):
                self.sender.raw_line('PONG ' + line.split(' ')[1])
                continue

            srv, code, me, msg = line.split(' ', 3)
            if code == '001':
                self.is_connected = True
                break  # Successful connection
            elif code == '433':
                # TODO: change to altnick
                self.nick += '_'
                self.sender.raw_line('NICK {0}'.format(self.nick))

        self.receiver.start()
        self.sender.start()
        logger.debug('Start receiver and sender threads')
        self.on_connect()

    def disconnect(self, quitmsg=None):
        """Disconnect from the server with an optional quit message.
        The on_disconnect event will be called when done.
        """
        self.sender.raw_line('QUIT :{0}'.format(quitmsg if quitmsg else ''))
        self.receiver.disconnect()

    def on_disconnect(self):
        """Overridden by IRCBot/client.
        """
        pass

    def on_connect(self):
        """Overridden by IRCBot/client.
        """
        pass

    def line_received(self, line):
        """Called on every line received from the server.
        Overridden in IRCBot to call events.
        """
        if line.startswith('PING '):
            self.sender.raw_line('PONG ' + self.nick)


class ConnectException(BaseException):

    def __init__(self, msg=None):
        if not msg:
            self.msg = 'An exception occurred connecting to the IRC server.'
        else:
            self.msg = msg

    def __str__(self):
        return repr(self.msg)


class AlreadyConnectedException(ConnectException):

    def __init__(self):
        self.msg = 'Already connected to a server. Disconnect ' \
                   'before trying a new connection.'


class SSLNotAvailableException(ConnectException):

    def __init__(self):
        self.msg = 'SSL module is not available.'
