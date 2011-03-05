from linehandler import LineHandler

class LineReceiver(LineHandler):
    def __init__(self, bot, socket):
        LineHandler.__init__(self, bot, socket)
        
    def _read(self):
        """Read data from socket, stripping CR/LF
        """
        
        line = self._fo.readline()
        if not line:
            return None
        
        if line[-2:] == self._CRLF:
            line = line[-2:]
        
        return line
        
    def run(self):
        while(self._bot.is_connected):
            line = self._read()
            if not line:
                #Connection was dropped, disconnect
                self._socket.close()
                self._bot.is_connected = False
                self._bot.on_disconnect()
                self._bot.logger.log('Disconnected from {0}'.format(self._bot.server))
                
            try:
                self._bot.line_received(line)
            except Exception as exc:
                #TODO: Unhandled exception in bot's line receiver
                pass
