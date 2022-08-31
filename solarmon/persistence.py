class CsvFile:

    def __init__(self, path):
        self._file = open(path, 'w')
        self._heading_written = False

    def write(self, sample):
        if not self._heading_written:
            self._file.write(','.join([x[0] for x in sample]) + '\n')
            self._heading_written = True
        self._file.write(','.join([str(x[1]) for x in sample]) + '\n')
        self._file.flush()
