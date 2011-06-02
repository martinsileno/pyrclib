class User(object):
    """Represents a user on IRC.
    """
    def __init__(self, nick, ident=None, host=None):
        self.nick = nick
        self.ident = ident
        self.host = host
    
    def __str__(self):
        return '{}!{}@{}'.format(self.nick, self.ident, self.host)
