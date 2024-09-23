import logging


class Sample:

    def __init__(self, device):
        self.device = device
        self.values = [None] * len(device.params())
        self.exception = None

    def load(self, values):
        self.values = [None if x == '' else x for x in values]

    def invalidate(self, exception):
        self.exception = exception

    def is_error(self):
        return self.exception is not None

    def error(self):
        return str(self.exception)


def read_from(device):
    sample = Sample(device)
    try:
        sample.load(device.read())
    except Exception as e:
        sample.invalidate(e)
        logging.error('Could not read from "%s", reason: %s', device.name, e)
        logging.info('Reconfiguring device after a bad response...')
        device.reconfigure()
    return sample
