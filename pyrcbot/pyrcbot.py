import socket
import time
from datetime import datetime

from pyrcbot import events
import pyrcbot.ircconstants as const
from pyrcbot.linereceiver import LineReceiver
from pyrcbot.linesender import LineSender
from pyrcbot.logger import Logger

class PyrcBot(object):
    def __init__(self):
        self.delay = 1000
        self.logger = Logger()
        self.nick = 'C1-PIRL8'
        self.user = 'c'
        self.realname = 'Python IRC bot'
        self.is_connected = False
        self.dispatcher = events.EventDispatcher(self)
        
        #CTCP replies, should be set in a separate config file
        self.reply_clientinfo = 'CLIENTINFO FINGER PING SOURCE TIME USERINFO VERSION'
        self.reply_finger = 'Don\'t finger me, pervert!'
        self.reply_source = 'http://trac.1way.it/'
        self.reply_userinfo = ''
        self.reply_version = 'Pyrcbot'
    
    def connect(self, address, port=6667, password=None, useSSL=False):
        """Connect to the specified IRC server.
        - address: the address of the server
        - port: port of the server, defaults to 6667
        - password: if a password is required to connect
        - useSSL: use a secure connection with SSL
        """
        self.server = address
        if self.is_connected:
            raise AlreadyConnectedException()
        
        self.logger.log('Connecting to server: {0}'.format(address))
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((address, port)) # TODO: Exceptions?
        
        # Using SSL?
        if useSSL:
            try:
                import ssl
            except ImportError:
                raise SSLNotAvailableException()
            s = ssl.wrap_socket(s)
        self.receiver = LineReceiver(self, s)
        
        # Manually handle connection to the server
        self.sender = LineSender(self, s, self.delay)
        
        if password:
            self.sender.raw_line('PASS {0}'.format(password))
        
        self.sender.raw_line('NICK {0}'.format(self.nick))
        self.sender.raw_line('USER {0} * * :{1}'.format(self.user, self.realname))
        
        fo = s.makefile('rb')
        while True:
            line = fo.readline()
            if not line:
                break
            
            line = line.decode()
            if line[-2:] == '\r\n':
                line = line[:-2]
            
            if line.startswith('PING') or line.startswith('PONG'):
                self.sender.raw_line('PONG ' + line.split(' ')[1])
                continue
            
            srv, code, me, msg = line.split(' ', 3)
            if code == const.RPL_MYINFO:
                self.is_connected = True
                break # Successful connection
            elif code == const.ERR_NICKNAMEINUSE:
                #TODO: change to altnick
                self.nick += '_'
                self.sender.raw_line('NICK {0}'.format(self.nick))
            
            
            self.logger.log(line)
        
        self.receiver.start()
        self.sender.start()
    
    def disconnect(self, quitmsg=None):
        """Disconnect from the server with an optional quit message.
        The on_disconnect event will be called when done.
        """
        self.sender.raw_line('QUIT :{0}'.format(quitmsg if quitmsg else ''))
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
    
    #===========================================================================
    # Events
    #===========================================================================
    
    def on_disconnect(self):
        """Called on disconnection from a server, can be overridden as required.
        """
        pass
    
    def on_serverping(self):
        """Called on a PING request from the IRC server.
        Shouldn't be overridden...
        """
        self.sender.raw_line('PONG ' + self.nick)
    
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
    
    def on_part(self, user, channel, reason=None):
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
    
    #===========================================================================
    # -- CTCP events -- #
    # All CTCP descriptions are taken from:
    # http://www.irchelp.org/irchelp/rfc/ctcpspec.html
    #===========================================================================
    
    def on_CTCP_clientinfo(self, sender, target, arg):
        """This is for client developers use to make it easier to show other
        client hackers what a certain client knows when it comes to CTCP. The
        replies should be fairly verbose explaining what CTCP commands are
        understood.
        """
        self.ctcpreply(sender['nick'], 'CLIENTINFO', self.reply_clientinfo)
    
    def on_CTCP_finger(self, sender, target, arg):
        """This is used to get a user's real name, and perhaps also the idle time
        of the user (this usage has been obsoleted by enhancements to the IRC
        protocol).
        """
        self.ctcpreply(sender['nick'], 'FINGER', self.reply_finger)
    
    def on_CTCP_ping(self, sender, target, arg):
        """Ping is used to measure the time delay between clients on the IRC
        network.
        The replying client sends back an identical message inside a notice.
        """
        self.ctcpreply(sender['nick'], 'PING', arg)
    
    def on_CTCP_source(self, sender, target, arg):
        """This is used to get information about where to get a copy of the
        client.
        """
        self.ctcpreply(sender['nick'], 'SOURCE', self.reply_source)
    
    def on_CTCP_time(self, sender, target, arg):
        """Time queries are used to determine what time it is where another
        user's client is running.
        """
        #TODO: allow custom reply.
        self.ctcpreply(sender['nick'], 'TIME', str(datetime.now())[:19])
    
    def on_CTCP_userinfo(self, sender, target, arg):
        """This is used to transmit a string which is settable by the user (and
        never should be set by the client).
        """
        if self.reply_userinfo:
            self.ctcpreply(sender['nick'], 'USERINFO', self.reply_userinfo)
    
    def on_CTCP_version(self, sender, target, arg):
        """This is used to get information about the name of the other client and
        the version of it.
        """
        self.ctcpreply(sender['nick'], 'VERSION', self.reply_version)
    
    def on_CTCPREPLY_ping(self, sender, target, arg):
        """Triggered when someone replies to our CTCP ping query.
        """
        pass
    
    #===========================================================================
    # Mode events
    #===========================================================================
        
    def on_modechange(self, *args):
        """Called whenever a mode is changed.
        Subclasses should override this method to call appropriate events
        for their server's IRCd.
        See also: ticket #4.
        """
        pass

    ### IRC Commands ###
    def join(self, channel, key=None):
        """Joins a channel with an optional key.
        This method must not be overridden.
        """
        s = 'JOIN ' + channel
        if key:
            s += ' ' + key
        
        self.sender.raw_line(s)
        
    def part(self, channel, reason=None):
        """Parts from a channel with an optional reason.
        This method must not be overridden.
        """
        s = 'PART ' + channel
        if reason:
            s += ' :' + reason
        
        self.sender.raw_line(s)
    
    def ctcpreply(self, target, type, reply=None):
        """Sends a reply (a notice) to a CTCP request.
        This method must not be overridden.
        """
        r = '{0}{1}{0}'.format(chr(1), 
                            type if not reply else '{0} {1}'.format(type, reply))
        self.notice(target, r)
    
    def ping(self, target, ts=None):
        """Sends a CTCP Ping request to a target.
        """
        self.ctcpquery(target, 'PING', ts if ts else int(time.time()))
    
    def ctcpquery(self, target, type, args=None):
        """Sends a CTCP request (privmsg) to a target.
        This method must not be overridden.
        """
        r = '{0}{1}{2}{0}'.format(chr(1), type, ' {0}'.format(args) if args else '')
        self.privmsg(target, r)
    
    def notice(self, target, msg):
        """Sends a notice to a channel or a user.
        This method must not be overridden.
        """
        self.sender.add('NOTICE {0} :{1}'.format(target, msg))
    
    def privmsg(self, target, msg):
        """Sends a message to a channel or a user.
        This method must not be overridden. 
        """
        self.sender.add('PRIVMSG {0} :{1}'.format(target, msg))
    
    def identify(self, password):
        """Identifies the bot to NickServ.
        This method must not be overridden.
        """
        self.sender.raw_line('NICKSERV IDENTIFY {0}'.format(password))
    
    def invite(self, channel, user):
        """Used to invite someone in a channel.
        """
        self.sender.raw_line('INVITE {0} {1}'.format(user, channel))
    
    def kick(self, channel, user, reason=None):
        """Used to kick a user out of a channel with an optional reason.
        """
        s = 'KICK {0} {1}'.format(channel, user)
        if reason:
            s += ' :' + reason
        
        self.sender.raw_line(s)
    
    def voice(self, channel, user):
        """Voices a user (or more, if user is a list) in a channel.
        """
        m = 'v'
        if isinstance(user, list):
            m = m * len(user)
        else:
            user = [user]
        self.set_mode(channel, m, user)
    
    def op(self, channel, user):
        """Ops a user (or more, if user is a list) in a channel.
        """
        m = 'o'
        if isinstance(user, list):
            m = m * len(user)
        else:
            user = [user]
        self.set_mode(channel, m, user)
    
    def nickchange(self, newnick):
        """This method changes our bot's nick. It could fail, for example
        if the new nickname is not available.
        This method must not be overridden.
        """
        self.sender.raw_line('NICK {0}'.format(newnick))
        
    def topic(self, channel, newtopic=None):
        """This method is used to change a channel's topic.
        If no newtopic is given, the server will reply with the current topic.
        This method must not be overridden.
        """
        s = 'TOPIC ' + channel
        if newtopic:
            s += ' :' + newtopic
        
        self.sender.raw_line(s)
    
    def set_mode(self, channel, mode, args=None):
        """Set a mode (or more than one) in a channel with optional arguments.
        - args is a list.
        """
        s = 'MODE {0} +{1}'.format(channel, mode)
        if args:
            s += ' ' + ' '.join(args)
        
        self.sender.raw_line(s)
        
    def unset_mode(self, channel, mode, args=None):
        """Removes a mode (or more than one) from a channel with optional 
        arguments.
        - args is a list.
        """
        s = 'MODE {0} -{1}'.format(channel, mode)
        if args:
            s += ' ' + ' '.join(args)
        
        self.sender.raw_line(s)
    
### Connect Exceptions ###
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
        self.msg = 'Already connected to a server. Disconnect before trying a \
        new connection.'

class SSLNotAvailableException(ConnectException):
    def __init__(self):
        self.msg = 'SSL module is not available.'
