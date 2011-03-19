import random
import string

from pyrcbot import PyrcBot

class NiceBot(PyrcBot):
    def __init__(self):
        PyrcBot.__init__(self)
    
    def on_privmsg(self, sender, channel, message):
        if channel == '#1way' and message == '\\o/':
            self.privmsg(channel, '\\\\o \\o/ o//')
        if message.lower() == 'hi nicebot' or message.lower() == 'hey nicebot':
            self.privmsg(channel, 'Hi {0}!'.format(sender['nick']))
        if message == 'test':
            self.disconnect()
        if message == 'nickchange':
            N = 15
            self.nickchange(''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for x in range(N)))
        if message == 'part':
            self.part('#1way', 'pyrcbot <3')
        elif message == 'topic':
            self.topic('#1way')
        elif message == 'ctopic':
            self.topic('#1way', 'new topic provided by pyrcbot')
        elif message == 'invite':
            self.invite('#1way', 'martin')
        elif message == 'kick':
            self.kick('#1way', 'ma')
        elif message == 'rkick':
            self.kick('#1way', 'ma', 'kick sponsored by 1way.it')
        elif message == 'mvoice':
            self.voice('#1way', ['martin', 'NiceBot'])
        elif message == 'voice':
            self.voice('#1way', 'martin')

if __name__ == '__main__':
    p = NiceBot()
    p.nick = 'NiceBot'
    #p.connect('irc.undernet.org', 6667)
    #p.join('#duawhucfe')
    p.connect('1way.it', 42666, useSSL=True)
    p.identify('maipassw0rd')
    p.join('#1way')
        