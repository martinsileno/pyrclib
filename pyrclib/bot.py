import logging
import re
import time
from collections import deque
from datetime import datetime
from operator import itemgetter

import pyrclib
from pyrclib.channels import Channel
from pyrclib.connection import IRCConnection
from pyrclib.events import EventDispatcher
from pyrclib.user import User


class IRCBot(IRCConnection):

    def __init__(self, nick, user, realname):
        logging.basicConfig(
            format='%(asctime)s [%(levelname)8s] %(name)12s - %(message)s',
            level=logging.INFO,
        )
        IRCConnection.__init__(self, nick, user, realname)
        self.version = pyrclib.__version__
        self.delay = 1000
        self.dispatcher = EventDispatcher(self)
        self.protocol = {}

        # Used to queue /WHO requests
        self.pending_who = deque()

        # User and channel lists
        self.channels = {}
        self.users = {}

        self.reply_clientinfo = 'CLIENTINFO FINGER PING SOURCE TIME ' \
                                'USERINFO VERSION'
        self.reply_finger = 'Don\'t finger me, pervert!'
        self.reply_source = 'https://github.com/martinsileno/pyrclib'
        self.reply_userinfo = ''
        self.reply_version = 'pyrclib v%s' % self.version

    def line_received(self, line):
        """Called on every line received from the server.
        This method must not be overridden.
        """
        if line.startswith('PING '):
            self.on_serverping()
            return

        self.dispatcher.dispatch(line)

    # ==========================================================================
    # Raw events
    # Raw numerics documentation from: http://www.mirc.net/raws/
    # ==========================================================================

    def raw_005(self, *params):
        """Parse RPL_ISUPPORT (numeric 005) to understand this IRCd's protocol
        implementation. Otherwise, our client would fail to interpret server
        replies or modes changes.

        Referenced document: http://www.irc.org/tech_docs/005.html
        """
        for par in params[:-1]:
            param, sep, value = par.partition('=')
            if param == 'PREFIX':
                # A list of channel modes a person can get and the respective
                # prefix a channel or nickname will get in case the person
                # has it.
                # The order of the modes goes from most powerful to least
                # powerful.
                # Those prefixes are shown in the output of the WHOIS, WHO and
                # NAMES command.
                regex = re.compile('\((\w+)\)(.*)')
                r = regex.search(value)
                modes, symbols = r.groups()
                zipped = zip(modes, symbols)
                self.protocol['prefixes'] = list(zipped)
            elif param == 'CHANTYPES':
                # The supported channel prefixes.
                self.protocol['chantypes'] = value
            elif param == 'CHANMODES':
                # This is a list of channel modes according to 4 types.
                #  modes_target
                #    Mode that adds or removes a nick or address to a list.
                #    Always has a parameter.
                #  modes_param
                #    Mode that changes a setting and always has a parameter.
                #  modes_setparam
                #    Mode that changes a setting and only has a parameter
                #    when set.
                #  modes_noparam
                #    Mode that changes a setting and never has a parameter.
                (self.protocol['modes_target'], self.protocol['modes_param'],
                 self.protocol['modes_setparam'],
                 self.protocol['modes_noparam']) = value.split(',')
            elif param == 'MODES':
                # Maximum number of channel modes with parameter allowed per
                # MODE command.
                self.protocol['maxmodes'] = int(value)
            elif param == 'NICKLEN':
                # Maximum nickname length.
                self.protocol['maxnicklength'] = int(value)
            elif param == 'NETWORK':
                # The IRC network name.
                self.network = value
            elif param == 'EXCEPTS':
                # The server support ban exceptions (e mode).
                # See RFC 2811 for more information.
                self.protocol['supports_excepts'] = True
            elif param == 'INVEX':
                # The server support invite exceptions (+I mode).
                # See RFC 2811 for more information.
                self.protocol['supports_invex'] = True
            elif param == 'WALLCHOPS':
                # The server supports messaging channel operators
                self.protocol['wallchops'] = True
            elif param == 'WALLVOICES':
                # Notice to +#channel goes to all voiced persons.
                self.protocol['wallvoices'] = True
            elif param == 'STATUSMSG':
                # The server supports messaging channel member
                # who have a certain status or higher.
                # The status is one of the letters from PREFIX.
                self.protocol['statusmsg'] = value
            elif param == 'CASEMAPPING':
                # Case mapping used for nick- and channel name comparing.
                self.protocol['casemapping'] = value
            elif param == 'ELIST':
                # The server supports extentions for the LIST command.
                # The tokens specify which extention are supported.
                self.protocol['elist'] = value
            elif param == 'TOPICLEN':
                # Maximum topic length.
                self.protocol['topiclen'] = int(value)
            elif param == 'KICKLEN':
                # Maximum kick comment length.
                self.protocol['kicklen'] = int(value)
            elif param == 'CHANNELLEN':
                # Maximum channel name length.
                self.protocol['channellen'] = int(value)
            elif param == 'SILENCE':
                # The server support the SILENCE command.
                # The number is the maximum number of allowed entries in the
                # list.
                self.protocol['max_silencelist'] = int(value)
            elif param == 'RFC2812':
                # Server supports RFC 2812 features.
                self.protocol['rfc2812'] = True
            elif param == 'PENALTY':
                # Server gives extra penalty to some commands instead of the
                # normal
                # 2 seconds per message and 1 second for every 120 bytes in a
                # message.
                self.protocol['penalty'] = True
            elif param == 'FNC':
                # Forced nick changes: The server may change the nickname
                # without the client sending a NICK message.
                self.protocol['fnc'] = True
            elif param == 'SAFELIST':
                # The LIST is sent in multiple iterations so send queue won't
                # fill and kill the client connection.
                self.protocol['safelist'] = True
            elif param == 'AWAYLEN':
                # The max length of an away message.
                self.protocol['awaylen'] = int(value)
            elif param == 'USERIP':
                # The USERIP command exists.
                self.protocol['userip'] = True
            elif param == 'CPRIVMSG':
                # The CPRIVMSG command exists, used for mass messaging people in
                # specified channel (CPRIVMSG channel nick,nick2,... :text)
                self.protocol['cprivmsg'] = True
            elif param == 'CNOTICE':
                # The CNOTICE command exists, just like CPRIVMSG.
                self.protocol['cnotice'] = True
            elif param == 'MAXNICKLEN':
                # Maximum length of nicks the server will send to the client?
                self.protocol['maxnicklen'] = int(value)
            elif param == 'MAXTARGETS':
                # Maximum targets allowed for PRIVMSG and NOTICE commands.
                self.protocol['maxtargets'] = int(value)
            elif param == 'KNOCK':
                # The KNOCK command exists.
                self.protocol['knock'] = True
            elif param == 'WHOX':
                # The WHO command uses WHOX protocol.
                self.protocol['whox'] = True
            elif param == 'CALLERID':
                # The server supports server side ignores via the +g user mode.
                self.protocol['callerid'] = True

    def raw_315(self, channel, endofwho):
        """This is sent at the end of a WHO request.
        """
        self.pending_who.popleft()  # Oldest /WHO done, remove it
        if len(self.pending_who) > 0:
            # Other /WHO request(s) waiting, send the oldest one
            self.sender.raw_line('WHO {0}'.format(self.pending_who[0]))

    def raw_324(self, channel, modes, args=None):
        """This is returned for a MODE request.
        """
        # TEMPORARY: we are currently ignoring modes parameters!
        self.channels[channel].modes = modes[1:]

    def raw_329(self, channel, time):
        """This is returned as part of a MODE request,
        giving you the time the channel was created.
        """
        self.channels[channel].creationdate = datetime.fromtimestamp(
            float(time))

    def raw_331(self, channel, msg):
        """This is returned for a TOPIC request if the channel has no current topic.
        On JOIN, if a channel has no topic, this is not returned.
        Instead, no topic-related replies are returned.
        """
        self.channels[channel].topic.reset()

    def raw_332(self, channel, topic):
        """This is returned for a TOPIC request or when you JOIN,
        if the channel has a topic.
        """
        self.channels[channel].topic.text = topic

    def raw_333(self, channel, nick, time):
        """This is returned for a TOPIC request or when you JOIN,
        if the channel has a topic.
        """
        if '!' and '@' in nick:
            # sometimes it's just a nick and not a full nick!user@host
            self.channels[channel].topic.set_by = User.from_mask(nick)
        self.channels[channel].topic.date = datetime.fromtimestamp(float(time))

    def raw_352(self, chan, ident, host, server, nick, status, hopsname):
        """This is returned by a WHO request, one line for each user that is
        matched.
        """
        hops, realname = hopsname.split(' ', 1)
        self.users[nick].ident = ident
        self.users[nick].host = host
        self.users[nick].realname = realname
        # TODO: parse flags:
        # - away status
        # - ircop status

    def raw_353(self, bla, channel, names):
        """This is returned for a NAMES request for a channel, or when you
        initially join a channel.
        It contains a list of every user on the channel.
        """
        prefixes = list(map(itemgetter(1), self.protocol['prefixes']))
        for name in names.split(' '):
            if name[0] not in prefixes:
                mode = ''
            else:
                mode = name[0]
                st = 1
                for c in name[1:]:
                    if c in prefixes:
                        mode += c
                        st += 1
                    else:
                        break

                name = name[st:]

            self.users[name] = User(name)
            self.channels[channel].users[name] = mode

    def raw_366(self, channel, msg):
        """This is returned at the end of a NAMES list, after all
        visible names are returned.
        """
        pass

    def raw_unknown(self, numeric, *args):
        pass

    # ==========================================================================
    # Private events
    #
    # ==========================================================================

    def _pre_join(self, user, channel):
        """Adds the user to the channel user list.
        If we are joining a channel, add this channel to ours, send a MODE
        request to get the channel modes and a WHO request to get ident/host
        of unknown users.
        """
        self.users[user.nick] = user
        if user.nick == self.nick:
            self.channels[channel] = Channel(channel)
            self.sender.raw_line('MODE {0}'.format(channel))
            self.request_who(channel)

        self.channels[channel].users[user.nick] = ''
        self.on_join(user, channel)

    def _pre_part(self, user, channel, reason=None):
        """Removes the user from the channel user list.
        """
        if user.nick == self.nick:
            del self.channels[channel]
        else:
            del self.channels[channel].users[user.nick]
            # remove him from global user list only if we don't share any chan.
            if self.get_comchans(user.nick) == []:
                del self.users[user.nick]

        self.on_part(user, channel, reason)

    def _pre_nick(self, user, newnick):
        """Changes a user's nick.
        """
        oldnick = user.nick
        if oldnick == self.nick:
            self.nick = newnick

        for chan in self.get_comchans(user.nick):
            chan.renameuser(oldnick, newnick)

        del self.users[oldnick]
        user.nick = newnick
        self.users[newnick] = user
        self.on_nickchange(oldnick, newnick)

    def _pre_kick(self, sender, channel, nick, reason=None):
        """Removes a user from a channel's user list when he gets kicked.
        """
        del self.channels[channel].users[nick]
        if self.get_comchans(nick) == []:
            del self.users[nick]

        self.on_kick(sender, nick, channel, reason)

    def _pre_kill(self, killer, victim, message):
        """We were killed by someone, disconnect.
        """
        if victim == self.nick:  # is this really needed?
            self.receiver.disconnect()

        self.on_kill(killer, victim, message)

    def _pre_quit(self, user, reason=None):
        """Removes a user from list when he quits.
        """
        nick = user.nick
        del self.users[nick]

        for chan in self.get_comchans(user.nick):
            del chan.users[nick]

        self.on_quit(user, reason)

    def _pre_topic(self, sender, channel, newtopic):
        """Topic tracking.
        """
        self.channels[channel].topic.text = newtopic
        self.channels[channel].topic.set_by = sender
        self.channels[channel].topic.date = datetime.now()

        self.on_topicchange(sender, channel, newtopic)

    def _set_prefix(self, channel, m, target):
        """Adds a prefix (like op, voice etc.) to a user in a channel.
        """
        s = dict(self.protocol['prefixes'])[m]
        self.channels[channel].users[target] += s

    def _unset_prefix(self, channel, m, target):
        """Removes a prefix (like op, voice etc.) from a user in a channel.
        """
        s = dict(self.protocol['prefixes'])[m]
        current = self.channels[channel].users[target]
        self.channels[channel].users[target] = current.replace(s, '')

    def _pre_set_mode(self, user, channel, mode, target=None):
        """Syncs channels modes with mode changes.
        """
        if mode not in map(itemgetter(0), self.protocol['prefixes']):
            self.channels[channel].modes += mode

        self.on_set_mode(user, channel, mode, target)

    def _pre_unset_mode(self, user, channel, mode, target=None):
        """Syncs channels modes with mode changes.
        """
        if mode not in map(itemgetter(0), self.protocol['prefixes']):
            current = self.channels[channel].modes
            self.channels[channel].modes = current.replace(mode, '')

        self.on_unset_mode(user, channel, mode, target)

    # ==========================================================================
    # Public events
    #
    # ==========================================================================

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
        """Called when a message is received.
        DON'T USE, USE on_channel_message or on_private_message
        """
        pass

    def on_channel_message(self, sender, channel, message):
        """Called when a channel message is received.
        """
        pass

    def on_private_message(self, sender, message):
        """Called when a private message is received.
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

    def on_kill(self, killer, victim, message):
        """Some evil user killed us.
        """
        pass

    def on_set_mode(self, user, channel, mode, target=None):
        """Called when a mode is set.
        """
        pass

    def on_unset_mode(self, user, channel, mode, target=None):
        """Called when a mode is unset.
        """
        pass

    def on_unknown(self, *args):
        """An unknown event happened! We don't know how to process it.
        """
        pass

    # ==========================================================================
    # -- CTCP events -- #
    # All CTCP descriptions are taken from:
    # http://www.irchelp.org/irchelp/rfc/ctcpspec.html
    # ==========================================================================

    def on_CTCP_clientinfo(self, sender, target, arg):
        """This is for client developers use to make it easier to show other
        client hackers what a certain client knows when it comes to CTCP. The
        replies should be fairly verbose explaining what CTCP commands are
        understood.
        """
        self.ctcpreply(sender.nick, 'CLIENTINFO', self.reply_clientinfo)

    def on_CTCP_finger(self, sender, target, arg):
        """This is used to get a user's real name, and perhaps also the idle time
        of the user (this usage has been obsoleted by enhancements to the IRC
        protocol).
        """
        self.ctcpreply(sender.nick, 'FINGER', self.reply_finger)

    def on_CTCP_ping(self, sender, target, arg):
        """Ping is used to measure the time delay between clients on the IRC
        network.
        The replying client sends back an identical message inside a notice.
        """
        self.ctcpreply(sender.nick, 'PING', arg)

    def on_CTCP_source(self, sender, target, arg):
        """This is used to get information about where to get a copy of the
        client.
        """
        self.ctcpreply(sender.nick, 'SOURCE', self.reply_source)

    def on_CTCP_time(self, sender, target, arg):
        """Time queries are used to determine what time it is where another
        user's client is running.
        """
        # TODO: allow custom reply.
        self.ctcpreply(sender.nick, 'TIME', str(datetime.now())[:19])

    def on_CTCP_userinfo(self, sender, target, arg):
        """This is used to transmit a string which is settable by the user (and
        never should be set by the client).
        """
        if self.reply_userinfo:
            self.ctcpreply(sender.nick, 'USERINFO', self.reply_userinfo)

    def on_CTCP_version(self, sender, target, arg):
        """This is used to get information about the name of the other client and
        the version of it.
        """
        self.ctcpreply(sender.nick, 'VERSION', self.reply_version)

    def on_CTCPREPLY_ping(self, sender, target, arg):
        """Triggered when someone replies to our CTCP ping query.
        """
        pass

    # IRC Commands

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
        r = '{0}{1}{0}'.format(
            chr(1), type if not reply else '{0} {1}'.format(type, reply))
        self.notice(target, r)

    def ping(self, target, ts=None):
        """Sends a CTCP Ping request to a target.
        """
        self.ctcpquery(target, 'PING', ts if ts else int(time.time()))

    def ctcpquery(self, target, type, args=None):
        """Sends a CTCP request (privmsg) to a target.
        This method must not be overridden.
        """
        r = '{0}{1}{2}{0}'.format(
            chr(1), type, ' {0}'.format(args) if args else '')
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
            m *= len(user)
        else:
            user = [user]
        self.set_mode(channel, m, user)

    def op(self, channel, user):
        """Ops a user (or more, if user is a list) in a channel.
        """
        m = 'o'
        if isinstance(user, list):
            m *= len(user)
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

    def request_who(self, target):
        """Puts a /WHO request in a queue. Sends it if the queue is empty.
        """
        self.pending_who.append(target)
        if len(self.pending_who) == 1:
            self.sender.raw_line('WHO {0}'.format(target))

    def get_comchans(self, nick):
        """Returns a list of channels our bot and this user are in.
            """
        comchans = []
        for bla, chan in self.channels.items():
            if nick in chan.users:
                comchans.append(chan)

        return comchans
