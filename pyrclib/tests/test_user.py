import unittest

from pyrclib.user import User


class UserTests(unittest.TestCase):

    def test_create_from_mask(self):
        mask = 'py-ctcp!ctcp@ctcp-scanner.rizon.net'
        user = User.from_mask(mask)
        self.assertEqual(user.nick, 'py-ctcp')
        self.assertEqual(user.ident, 'ctcp')
        self.assertEqual(user.host, 'ctcp-scanner.rizon.net')
