import socket
import events
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
        self.dispatcher = events.EventDispatcher(self)
    
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
        self.ls = LineSender(self, s)
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
        self.ls.start()
    
    def disconnect(self, quitmsg=None):
        """Disconnect from the server with an optional quit message.
        The on_disconnect event will be called when done.
        """
        self.ls.raw_line('QUIT :' + quitmsg if quitmsg else '')
        self.receiver.disconnect()
        
    def line_received(self, line):
        """Called on every line received from the server.
        This method must not be overridden.
        """
        if line.startswith('PING '):
            self.on_serverping()
            return
        
        self.dispatcher.dispatch(line)
    
    def _parse_nick(self, s):
        """Function to split nick!user@host into a dict with nick, user and host as keys.
        """
        u, host = s.split('@', 1)
        nick, user = u.split('!', 1)
        return {'nick': nick, 'user': user, 'host': host}
        
    ### Events ###
    def on_disconnect(self):
        """Called on disconnection from a server, can be overridden as required.
        """
        pass
    
    def on_serverping(self):
        """Called on a PING request from the IRC server.
        Shouldn't be overridden...
        """
        self.ls.raw_line('PONG ' + self.nick)
    
    def on_privmsg(self, sender, channel, message):
        """Called when a channel message is received.
        """
        pass
    
    def on_action(self, sender, channel, message):
        """Called when an action is received (/me does something).
        """
        pass
    
    def on_join(self, user, channel):
        """Called when someone (our bot included) joins a channel.
        """
        pass
    
    def on_part(self, user, channel, reason):
        """Called when someone (out bot included) parts from a channel.
        """
        pass
    
    def on_nickchange(self, oldnick, newnick):
        """Called when someone (our bot included) changes nick.
        """
        pass
    
    def on_notice(self, sender, target, message):
        """Called when a notice is received. Target can be a channel or our bot's nick.
        """
        pass
    
    def on_quit(self, user, reason):
        """Called when someone (our bot included) quits from IRC.
        """
        pass
    
    def on_kick(self, sender, target, channel, reason):
        """Called when someone (our bot included) gets kicked from a channel.
        """
        pass
    
    def on_topicchange(self, sender, channel, newtopic):
        """Called when someone changes channel topic.
        """
        pass
    
    def on_invite(self, sender, target, channel):
        """TODO
        """
        pass
    
    
    ### IRC Commands ###
    def join_channel(self, channel, key=None):
        """Joins a channel with an optional key.
        """
        s = 'JOIN ' + channel
        if key:
            s += ' ' + key
        
        self.ls.raw_line(s)
    
    def privmsg(self, target, msg):
        """Sends a message to a channel or a user.
        """
        self.msgqueue.add('PRIVMSG {0} :{1}'.format(target, msg))
    
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
    