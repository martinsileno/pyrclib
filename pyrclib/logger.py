from datetime import datetime

class Logger(object):
#    L_ERROR = 0
#    L_WARNING = 1
#    L_MESSAGE = 2
#    L_COMMAND = 3
    
    def __init__(self):
        pass
    
    def log(self, line):
        """Log a line using the specified method (stdout or file)
        """
        
        #TODO: log to file
        #TODO: different log levels, command, debug, error etc...
        print('%s %s' % (str(datetime.now())[:19], line))
