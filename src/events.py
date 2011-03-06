class EventDispatcher(object):
    """
    """
    def __init__(self, bot):
        self.bot = bot
        self.usermap = {
            'INVITE'     : self.bot.on_invite,
            'JOIN'       : self.bot.on_join,
            'KICK'       : self.bot.on_kick,
            'MODE'       : self._parse_mode,
            'NICK'       : self.bot.on_nickchange,
            'NOTICE'     : self.bot.on_notice,
            'PART'       : self.bot.on_part,
            'PRIVMSG'    : self._parse_privmsg,
            'QUIT'       : self.bot.on_quit,
            'TOPIC'      : self.bot.on_topicchange
            }
        
        self.ctcpmap = {
            'CLIENTINFO' : self.bot.on_CTCP_clientinfo,
            'FINGER'     : self.bot.on_CTCP_finger,
#            'HOST'       : self.bot.on_CTCP_host
#            'OS'         : self.bot.on_CTCP_os,
            'PING'       : self.bot.on_CTCP_ping,
            'SOURCE'     : self.bot.on_CTCP_source,
            'TIME'       : self.bot.on_CTCP_time,
            'USERINFO'   : self.bot.on_CTCP_userinfo,
            'VERSION'    : self.bot.on_CTCP_version,
            }
    
    def _parse_privmsg(self, sender, target, message):
        """Not all PRIVMSGs will trigger the on_privmsg event,
        in this function we'll check if it's actually a channel message 
        or a CTCP/action.
        """
        if message.startswith(chr(1)) and message.endswith(chr(1)):
            message = message[1:-1]
            if message.startswith('ACTION'):
                self.bot.on_action(sender, target, message.split(' ', 1)[1])
            else:
                if ' ' in message:
                    command, arg = message.split(' ', 1)
                else:
                    command, arg = message, ''
                if command in self.ctcpmap:
                    self.ctcpmap[command](sender, target, arg)
        else:
            self.bot.on_privmsg(sender, target, message)
    
    def _parse_mode(self, *args):
        """
        """
        pass
    
    def _parsemsg(self, s):
        """Breaks a message from an IRC server into its prefix, command, and arguments.
        From twisted.words.protocols.irc:
        http://twistedmatrix.com/documents/current/api/twisted.words.protocols.irc.html
        """
        prefix = ''
        trailing = []
        if s[0] == ':':
            prefix, s = s[1:].split(' ', 1)
        if s.find(' :') != -1:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
        else:
            args = s.split()
        command = args.pop(0)
        return prefix, command, args
    
    def dispatch(self, line):
        """This method calls the appropriate event for this line.
        """
        prefix, command, args = self._parsemsg(line)
        if '!' in prefix and '@' in prefix:
            u, host = prefix.split('@', 1)
            nick, user = u.split('!', 1)
            sender = {'nick': nick, 'user': user, 'host': host}
            if command in self.usermap:
                self.usermap[command](sender, *args)
            else:
                self.bot.on_unknown(sender, *args)
        else:
            #It's a server message
            #TODO: parse it!
            pass
