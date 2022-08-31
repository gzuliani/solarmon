class CsvFile:

    def __init__(self, path):
        self._file = open(path, 'w')

    def write_heading(self, names):
        self._file.write(','.join(names) + '\n')

    def write_values(self, values):
        self._file.write(','.join([str(x) for x in values]) + '\n')
        self._file.flush()
