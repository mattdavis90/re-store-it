import logging
import xmlrpclib
import time
import subprocess

from socket import gethostname

from mode import Mode
from helper import get_config, get_server_url, wrap_xmlrpc


class Restore(Mode):
    def _initialise(self, args):
        logging.debug('Starting client mode checks on config file')

        config = get_config(args.config_file)

        server_url = get_server_url(config)

        self._proxy = xmlrpclib.ServerProxy(server_url)
        self._hostname = gethostname()
        self._artifact = args.artifact
        self._version = args.version

        logging.debug('Client checks passed')

    def _add_arguments(self):
        self._parser.add_argument('artifact', metavar='ARTIFACT')
        self._parser.add_argument('version', metavar='VERSION')
        self._parser.add_argument('config_file', metavar='CONFIGFILE')

    def run(self):
        logging.debug('Retrieving artifact')

        filename, restore_command, binary = wrap_xmlrpc(self._proxy.get_version, self._hostname, self._artifact, self._version)

        with open(filename, 'wb') as handle:
            handle.write(binary.data)

        if restore_command:
            subprocess.call(restore_command, shell=True)

        logging.debug('Finished retrieving artifact')

    def stop(self):
        pass