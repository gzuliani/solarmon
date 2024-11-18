import datetime


class CsvFile:
    def __init__(self, name, path):
        self.name = name
        self._file = open(path, "w")
        self._columns = []

    def write(self, samples):
        names = [x.name for s in samples for x in s.device.params()]
        if names != self._columns:
            self._columns = names
            self._file.write(",".join(["local_time"] + self._columns) + "\n")
        local_time = datetime.datetime.now().isoformat()
        raw_data = [local_time] + [str(x) for s in samples for x in s.values]
        self._file.write(",".join([str(x) for x in raw_data]) + "\n")
        self._file.flush()
