class Channel(object):
    """Represents a channel we are in.
    """
    def __init__(self, name):
        self.name = name
        self.users = {}
    
    def renameuser(self, oldnick, newnick):
        """Called when a user changes nick.
        """
        user = self.users[oldnick]
        del self.users[oldnick]
        self.users[newnick] = user