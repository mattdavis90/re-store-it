import logging


class ClientMode(object):
    def __init__(self, config):
        logging.debug('Starting client mode checks on config file')

        if not config.has_section('client'):
            raise RuntimeError("Config file requires a 'client' section")

        if not config.has_option('client', 'server'):
            raise RuntimeError('Server not specified in config file')

        self._server = config.get('client', 'server')

        logging.debug('Client checks passed')

    def run(self):
        logging.debug('Starting XMLRPC client')

    def stop(self):
        logging.debug('Stopping XMLRPC client')
