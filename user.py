class User(object):
    """Represents a user on IRC.
    """
    def __init__(self, nick, ident, host):
        self.nick = nick
        self.ident = ident
        self.host = host
    
    def get_channels(self):
        """Returns a list of channels our bot and this user are in.
        """
        pass
    
    def __str__(self):
        return '{}!{}@{}'.format(self.nick, self.ident, self.host)