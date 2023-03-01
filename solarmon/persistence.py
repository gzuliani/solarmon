import datetime


class CsvFile:

    def __init__(self, name, path, column_names):
        self.name = name
        self._file = open(path, "w")
        self._file.write(",".join(["local_time"] + column_names) + "\n")

    def write(self, data):
        local_time = datetime.datetime.now().isoformat()
        raw_data = [local_time] + [str(x) for _, values in data for x in values]
        self._file.write(",".join([str(x) for x in raw_data]) + "\n")
        self._file.flush()
