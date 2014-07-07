import logging
import threading
import re
import xmlrpclib
import os
import subprocess
from datetime import datetime, timedelta
from socket import gethostname
from time import sleep

from mode import Mode
from helper import get_config, get_server_url, wrap_xmlrpc


def _tdelta(timestring):
    regex = "^((?P<weeks>\d+)w ?)?((?P<days>\d+)d ?)?((?P<hours>\d+)h ?)?((?P<minutes>\d+)m ?)?((?P<seconds>\d+)s ?)?$"
    kwargs = {}

    for k, v in re.match(regex, timestring).groupdict(default="0").items():
        kwargs[k] = int(v)

    return timedelta(**kwargs)


class Client(Mode):
    def _initialise(self, args):
        logging.debug('Starting client mode checks on config file')

        config = get_config(args.config_file)

        server_url = get_server_url(config)

        self._proxy = xmlrpclib.ServerProxy(server_url)
        self._hostname = gethostname()

        self._running = threading.Event()
        self._running.clear()

        logging.debug('Client checks passed')

    def _add_arguments(self):
        self._parser.add_argument('config_file', metavar='CONFIGFILE')

    def run(self):
        logging.debug('Starting XMLRPC client')

        self._running.set()

        config = wrap_xmlrpc(self._proxy.get_artifacts, self._hostname)

        if config:
            artifacts = []
            for name, properties in config.items():
                artifacts.append(Artifact(self._proxy, self._hostname, name, **properties))

            while self._running.is_set():
                for artifact in artifacts:
                    if artifact.ready_to_run():
                        artifact.run()

                sleep(1)

    def stop(self):
        logging.debug('Stopping XMLRPC client')

        self._running.clear()

class Artifact(object):
    def __init__(self, proxy, hostname, name, **kwargs):
        self._proxy = proxy
        self._hostname = hostname
        self._name = name

        self._file_based = kwargs.get('file_based', True)
        self._filename = kwargs.get('filename', '')
        self._backup_command = kwargs.get('backup_command', '').split(' ')
        self._cleanup = kwargs.get('cleanup', False)
        self._interval = _tdelta(kwargs.get('interval', '1h'))
        
        self._next_run = datetime.now()

        logging.info('Artifact %s - Loaded' % self._name)

    def ready_to_run(self):
        return self._next_run <= datetime.now()

    def run(self):
        logging.info('Artifact %s - Running' % self._name)

        self._next_run = datetime.now() + self._interval

        if not self._file_based:
            logging.debug('Artifact %s - Running backup command: %s' % (self._name, self._backup_command))
            
            subprocess.call(self._backup_command, shell=True)

        if os.path.isfile(self._filename):
            logging.debug('Artifact %s - Reading file' % self._name)
            
            with open(self._filename, 'rb') as handle:
                data = xmlrpclib.Binary(handle.read())
            
            logging.debug('Artifact %s - Sending file to XMLRPC server' % self._name)
            
            wrap_xmlrpc(self._proxy.store_version, self._hostname, self._name, data)

            if self._cleanup:
                logging.debug('Artifact %s - Removing file' % self._name)
                os.unlink(self._filename)

            logging.info('Artifact %s - Finished running' % self._name)