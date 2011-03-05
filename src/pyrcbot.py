import socket
import ircconstants as const
from linereceiver import LineReceiver
from linesender import LineSender, MessageQueue
from logger import Logger

class PyrcBot(object):
    def __init__(self):
        self.delay = 1000
        self.logger = Logger()
        self.nick = 'C1-PIRL8'
        self.realname = 'Python IRC bot'
        self.is_connected = False
        self.msgqueue = MessageQueue(self.delay)
    
    def connect(self, server, port=6667, password=None, useSSL=False):
        """Connect to the specified IRC server
        """        
        self.server = server
        if self.is_connected:
            raise AlreadyConnectedException()
        
        self.logger.log('Connecting to server: {0}'.format(server))
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server, port)) # Exceptions?
        self.receiver = LineReceiver(self, s)
        # Manually handle connection to the server
        fo = s.makefile('rb')
        self.ls = LineSender(self, s, self.msgqueue)
        if password:
            self.ls.raw_line('PASS {0}'.format(password))
        self.ls.raw_line('NICK {0}'.format(self.nick))
        self.ls.raw_line('USER {0} * * :{1}'.format(self.nick, self.realname))
        while True:
            line = fo.readline()
            if not line:
                break
            
            line = line.decode()
            if line[-2:] == '\r\n':
                line = line[:-2]
            
            srv, code, me, msg = line.split(' ', 3)
            if code == const.RPL_MYINFO:
                self.is_connected = True
                break # Successful connection
            elif code == const.ERR_NICKNAMEINUSE:
                #TODO: change to altnick
                self.nick += '_'
                self.ls.raw_line('NICK {0}'.format(self.nick))
            
            
            self.logger.log(line)
        
        self.receiver.start()
    
    def line_received(self, line):
        if line.startswith('PING '):
            self.on_serverping()
            return
        
    ### Events ###
    def on_disconnect(self):
        """Called on disconnection from a server, can be overridden as required.
        """
        pass
    
    def on_serverping(self):
        """Called on a PING request from the IRC server.
        """
        self.ls.raw_line('PONG ' + self.nick)
    
    ### Set bot properties ###
    def set_nick(self, nick):
        """Sets the nick the bot will use when connecting to the server.
        Must be set before connecting or it will use its default nick.
        """
        self.nick = nick
    
    def set_realname(self, name):
        """Sets the bot's realname. Must be set before connecting.
        """
        self.realname = name
        
    def set_delay(self, new_delay):
        self.msgqueue.set_delay(new_delay)

### Connect Exceptions ###
class ConnectException(BaseException):
    def __init__(self):
        self.msg = 'An exception occurred connecting to the IRC server.'
    def __str__(self):
        return repr(self.msg)

class AlreadyConnectedException(ConnectException):
    def __init__(self):
        self.msg = 'Already connected to a server. Disconnect before trying a \
        new connection.'
    