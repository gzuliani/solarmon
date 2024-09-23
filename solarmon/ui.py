import logging
import signal


class ShutdownRequest:

    def __init__(self):
        self.should_exit = False
        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def _exit(self, *args):
        logging.info('Received a shutdown request...')
        self.should_exit = True


