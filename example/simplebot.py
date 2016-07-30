from pyrclib.bot import IRCBot


class NiceBot(IRCBot):

    def on_privmsg(self, sender, channel, message):
        if message.lower() == 'hi nicebot' or message.lower() == 'hey nicebot':
            self.privmsg(channel, 'Hi {0}!'.format(sender.nick))


if __name__ == '__main__':
    p = NiceBot('NiceBot', 'nicebot', 'Nice Bot')
    p.connect('irc.eu.rizon.net', 6667)
    p.join('#mychannel')
