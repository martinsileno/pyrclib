class EventDispatcher(object):
    """
    """
    def __init__(self, bot):
        self.bot = bot
        self.usermap = {
            'PRIVMSG': self._parse_privmsg,
            'JOIN': bot.on_join,
            'PART': bot.on_part,
            'NICK': bot.on_nickchange,
            'NOTICE': bot.on_notice,
            'QUIT': bot.on_quit,
            'KICK': bot.on_kick,
            'MODE': self._parse_mode,
#            'TOPIC': bot.on_topic,
            'INVITE': bot.on_invite
            }
    
    def _parse_privmsg(self, sender, channel, message):
        """
        """
        self.bot.on_privmsg(sender, channel, message)
    
    def _parse_mode(self, *args):
        pass
    
    def _parsemsg(self, s):
        """Breaks a message from an IRC server into its prefix, command, and arguments.
        From twisted.words.protocols.irc
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
