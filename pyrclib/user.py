class User(object):
    """Represents a user on IRC.
    """

    def __init__(self, nick, ident=None, host=None, realname=None):
        self.nick = nick
        self.ident = ident
        self.host = host
        self.realname = realname

    def __str__(self):
        return '{}!{}@{}'.format(self.nick, self.ident, self.host)


def get_user_from_mask(mask):
    """Returns a User object from a string like 'nick!user@host'.
    """
    nick, h = mask.split('!', 1)
    ident, host = h.split('@', 1)

    return User(nick, ident, host)
