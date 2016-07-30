from pyrclib.user import User


class Channel(object):
    """Represents a channel we are in.
    """

    def __init__(self, name):
        self.name = name
        self.users = {}
        self.topic = Topic()
        # TODO: needs a better way to store modes,
        # what if the channel has a key/limit?
        self.modes = ''

    def renameuser(self, oldnick, newnick):
        """Called when a user changes nick.
        """
        modes = self.users[oldnick]
        del self.users[oldnick]
        self.users[newnick] = modes

    def __str__(self):
        return '{0} [+{1}]'.format(self.name, self.modes)

    def __contains__(self, item):
        if isinstance(item, User):
            if item.nick in self.users:
                return True
            return False

        for user in self.users.keys():
            if user.lower() == item.lower():
                return True

        return False


class Topic(object):
    """Represents a channel topic (text, set_by, date).
    """

    def __init__(self, text=None, set_by=None, date=None):
        self.text = text
        self.set_by = set_by
        self.date = date

    def reset(self):
        self.text = None
        self.set_by = None
        self.date = None

    def __str__(self):
        return self.text
