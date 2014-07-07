import logging
import xmlrpclib
import time

from socket import gethostname

from mode import Mode
from helper import get_config, get_server_url, wrap_xmlrpc


class List(Mode):
    def _initialise(self, args):
        logging.debug('Starting client mode checks on config file')

        config = get_config(args.config_file)

        server_url = get_server_url(config)

        self._proxy = xmlrpclib.ServerProxy(server_url)
        self._hostname = gethostname()
        
        self._artifacts = []
        if args.artifact:
            self._artifacts.append(args.artifact)

        logging.debug('Client checks passed')

    def _add_arguments(self):
        self._parser.add_argument('--artifact', metavar='ARTIFACT')
        self._parser.add_argument('config_file', metavar='CONFIGFILE')

    def run(self):
        logging.debug('Starting listing artifacts')

        if not self._artifacts:
            logging.info('No artifact given, listing all artifacts')
            config = wrap_xmlrpc(self._proxy.get_artifacts, self._hostname)

            if config:
                for name, properties in config.items():
                    self._artifacts.append(name)

            print 'Found %i Artifacts' % len(self._artifacts)

        for artifact in self._artifacts:
            versions = wrap_xmlrpc(self._proxy.get_versions, self._hostname, artifact)

            artifact_str = 'Artifact: %s (%d versions)' % (artifact, len(versions))

            print '-' * len(artifact_str)
            print artifact_str
            print '-' * len(artifact_str)

            for version in versions:
                print '\t%s [%s]' % (version['filename'], time.ctime(version['modified']))

        logging.debug('Finished listing artifacts')

    def stop(self):
        pass