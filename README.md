# Pyrclib #

pyrclib is a Python 3 IRC library. It can be used to make IRC bots, clients and bouncers.

### Features ###

* Event-driven
* Simple to use
* Supports SSL 

### Installation ###

To install just extract the files and run setup.py.

```python setup.py install```

You can verify the installation by opening a Python console and importing the module with

```
#!python
import pyrclib
```

# Example bot #

This example will show how to make a simple bot.

Our bot will just join a channel and will say `hi` to people who greet it with `hi nicebot` or `hey nicebot`.

```
#!python
from pyrclib.bot import IRCBot

class NiceBot(IRCBot):
	def __init__(self):
                self.nick = 'NiceBot'
                self.user = 'NiceBot'
		self.realname = 'NiceBot'
		IRCBot.__init__(self)
	
	def on_privmsg(self, sender, channel, message):
		if message.lower() == 'hi nicebot' or message.lower() == 'hey nicebot':
			self.privmsg(channel, 'Hi {0}!'.format(sender.nick))

if __name__ == '__main__':
	p = NiceBot()
	p.connect('irc.eu.rizon.net', 6667)
	p.join_channel('#mychannel')
```

```
#!rst
23:40 <@martin> hi NiceBot
23:40 < NiceBot> Hi martin!
```

## What does each line mean? ##

### Import ###

First, we need to import IRCBot module
```
#!python
from pyrclib.bot import IRCBot
```

### Initialization ###

```
#!python
class NiceBot(IRCBot):
	def __init__(self):
		IRCBot.__init__(self)
```

This part initializes our bot's internal properties.


### Overriding on_privmsg event ###

```
#!python
def on_privmsg(self, sender, channel, message):
```

With this, we are '''overriding''' the `on_privmsg` event.

This event is called on every channel message received.

IRCBot's default action is to just ignore this event, by overriding it we will add our custom behavior to our bot.

The three arguments to this function are:

* `sender`: an object containing sender's nick, user and host.

 For example, if sender was `martin!~abc@my.cool.host.net`, sender will be:
```
#!python
sender.nick = 'martin'
sender.user = '~abc'
sender.host = 'my.cool.host.net'
```

* `channel`: the channel this message was sent to.
* `message`: the content of this message.

### Start the bot and connect ###

The last part, after

```
#!python
if __name__ == '__main__':
```

will be executed when you run this python file with `python filename.py`.

Here we'll need to initialize the bot (see above)

```
#!python
	p = NiceBot()
```

make it connect to a server:

```
#!python
	p.connect('irc.eu.rizon.net', 6667)
```

make it join our channel:

```
#!python
	p.join_channel('#mychannel')
```