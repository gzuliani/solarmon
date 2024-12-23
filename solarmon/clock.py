import datetime
import time


class WallClock:
    def __init__(self):
        self._minute = self._current_minute()

    def wait_next_minute(self, abort_guard=None):
        while self._minute == self._current_minute():
            time.sleep(1)
            if abort_guard and abort_guard():
                break
        self._minute = self._current_minute()

    def _current_minute(self):
        return datetime.datetime.now().minute


class Timer:
    def __init__(self, interval):
        self._interval = interval
        self._start = time.time()

    def wait_next_tick(self, abort_guard=None):
        while time.time() - self._start < self._interval:
            time.sleep(1)
            if abort_guard and abort_guard():
                break
        self._start = time.time()
