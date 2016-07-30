from pyrclib.user import User


class EventDispatcher(object):
    """
    """

    def __init__(self, bot):
        self.bot = bot
        self.usermap = {
            'INVITE': self.bot.on_invite,
            'JOIN': self.bot._pre_join,
            'KICK': self.bot._pre_kick,
            'MODE': self._parse_mode,
            'NICK': self.bot._pre_nick,
            'NOTICE': self._parse_notice,
            'PART': self.bot._pre_part,
            'PRIVMSG': self._parse_privmsg,
            'QUIT': self.bot._pre_quit,
            'TOPIC': self.bot._pre_topic,
            'KILL': self.bot._pre_kill,
        }

        self.ctcpmap = {
            'CLIENTINFO': self.bot.on_CTCP_clientinfo,
            'FINGER': self.bot.on_CTCP_finger,
            # 'HOST': self.bot.on_CTCP_host
            # 'OS': self.bot.on_CTCP_os,
            'PING': self.bot.on_CTCP_ping,
            'SOURCE': self.bot.on_CTCP_source,
            'TIME': self.bot.on_CTCP_time,
            'USERINFO': self.bot.on_CTCP_userinfo,
            'VERSION': self.bot.on_CTCP_version,
        }

        self.ctcpreplymap = {
            'PING': self.bot.on_CTCPREPLY_ping,
        }

        self.rawsmap = {
            '005': self.bot.raw_005,
            '315': self.bot.raw_315,
            '324': self.bot.raw_324,
            '329': self.bot.raw_329,
            '331': self.bot.raw_331,
            '332': self.bot.raw_332,
            '333': self.bot.raw_333,
            '352': self.bot.raw_352,
            '353': self.bot.raw_353,
        }

        self.modesmap = {

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
            self.bot.on_privmsg(sender, target, message)  # DISABLE in 0.3.0
            if target == self.bot.nick:
                self.bot.on_private_message(sender, message)
            else:
                self.bot.on_channel_message(sender, target, message)

    def _parse_notice(self, sender, target, message):
        """Not all NOTICEs will trigger the on_notice event,
        in this function we'll check if it's actually a notice or a CTCP reply.
        """
        if message.startswith(chr(1)) and message.endswith(chr(1)):
            message = message[1:-1]
            if ' ' in message:
                command, arg = message.split(' ', 1)
            else:
                command, arg = message, ''
            if command in self.ctcpreplymap:
                self.ctcpreplymap[command](sender, target, arg)
        else:
            self.bot.on_notice(sender, target, message)

    def _parse_mode(self, user, channel, modes, *params):
        """Parse a modes string and call the appropriate event.
        """
        if channel == self.bot.nick:
            return  # TODO: We should also keep track of our user modes!

        modes_param = self.bot.protocol['modes_param']
        modes_setparam = self.bot.protocol['modes_setparam']
        modes_target = self.bot.protocol['modes_target']
        prefixes = dict(self.bot.protocol['prefixes'])
        params = list(params)

        for m in modes:
            if m == '+':
                adding = True
            elif m == '-':
                adding = False
            else:
                if m in modes_param or m in prefixes or \
                        (m in modes_setparam and adding):
                    target = params.pop(0)
                elif m in modes_target:
                    target = params.pop(0)
                    n, u, h = \
                        [target.split('!')[0]] + target.split('!')[1].split('@')
                    target = User(n, u, h)
                else:
                    target = None

                if adding:
                    if m in prefixes:
                        self.bot._set_prefix(channel, m, target)
                    self.bot._pre_set_mode(user, channel, m, target)
                else:
                    if m in prefixes:
                        self.bot._unset_prefix(channel, m, target)
                    self.bot._pre_unset_mode(user, channel, m, target)

    def _parsemsg(self, s):
        """Breaks a message from an IRC server into its prefix, command, and
        arguments.
        From twisted.words.protocols.irc:
        http://twistedmatrix.com/documents/current/api/twisted.words.protocols.irc.html
        """
        prefix = ''
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
            nick, h = prefix.split('!', 1)

            if nick in self.bot.users:
                sender = self.bot.users[nick]
            else:
                ident, host = h.split('@', 1)
                sender = User(nick, ident, host)

            if command in self.usermap:
                self.usermap[command](sender, *args)
            else:
                self.bot.on_unknown(sender, *args)
        else:
            # command = raw numeric
            if command in self.rawsmap:
                self.rawsmap[command](*args[1:])
            else:
                self.bot.raw_unknown(command, *args)
