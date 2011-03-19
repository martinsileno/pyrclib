from pyrcbot.linehandler import LineHandler

class LineReceiver(LineHandler):
    def __init__(self, bot, socket):
        LineHandler.__init__(self, bot, socket)
        
    def _read(self):
        """Read data from socket, stripping CR/LF
        """
        
        line = self._fo.readline()
        if not line:
            return None
        
        try: #Try decoding the string as UTF-8, if it fails, use latin-1
            line = line.decode()
        except UnicodeDecodeError as exc:
            line = line.decode('latin-1')
                
        if line[-2:] == self._CRLF:
            line = line[:-2]
        
        return line
    
    def disconnect(self):
        self._socket.close()
        self._bot.sender.stop()
        self._bot.is_connected = False
        self._bot.on_disconnect()
        self._bot.logger.log('Disconnected from {0}'.format(self._bot.server))
        
    def run(self):
        while(self._bot.is_connected):
            line = self._read()
            if not line:
                #Connection was dropped, disconnect
                self.disconnect()
            
            try:
                self._bot.logger.log(line)
                self._bot.line_received(line)
            except Exception as exc:
                #TODO: Unhandled exception in bot's line receiver
                raise exc
