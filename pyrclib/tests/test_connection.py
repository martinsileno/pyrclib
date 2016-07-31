import random
import unittest
from unittest.mock import Mock

from pyrclib.connection import IRCConnection


class ConnectionTests(unittest.TestCase):

    def setUp(self):
        self.nick = 'test_pybot-%d' % random.randint(1000,9999)
        self.user = 'test'
        self.realname = 'TestName'
        self.conn = IRCConnection(self.nick, self.user, self.realname)

    def test_initialization(self):
        self.assertEqual(self.conn.nick, self.nick)
        self.assertEqual(self.conn.user, self.user)
        self.assertEqual(self.conn.realname, self.realname)
        self.assertFalse(self.conn.is_connected)
        self.assertIsNone(self.conn.server)

    def test_connect(self):
        self.conn.receiver = Mock()
        self.conn.sender = Mock()
        self.conn.on_connect = Mock()
        self.conn.on_disconnect = Mock()
        self.conn.connect('irc.rizon.net', port=6667)
        self.assertTrue(self.conn.on_connect.called)
        self.assertTrue(self.conn.is_connected)
        self.conn.disconnect()
        self.assertTrue(self.conn.on_disconnect.called)
        self.assertFalse(self.conn.is_connected)
