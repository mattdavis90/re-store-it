import logging
from DocXMLRPCServer import DocXMLRPCServer
from DocXMLRPCServer import DocXMLRPCRequestHandler
import threading


class ServerMode(object):
    def __init__(self, config):
        logging.debug('Starting server mode checks on config file')

        self._clients = {}

        for section in config.sections():
            if not section == 'general':
                logging.debug('Found a client: %s' % section)

                if not config.has_option(section, 'artifacts'):
                    raise RuntimeError('Client sections require an artifacts option')

                artifacts_string = config.get(section, 'artifacts')
                artifacts = {}

                if artifacts_string == '':
                    raise RuntimeError('Artifacts list cannot be empty')

                for artifact in artifacts_string.split(','):
                    logging.debug('Found an artifact: %s' % artifact)

                    file_based = True
                    filename = ''
                    command = ''
                    cleanup = True
                    versions = 1
                    interval = 3600

                    if not config.has_option(section, artifact + '_file'):
                        raise RuntimeError("Artifacts must have at least a file specified. Error in client '%s'" % section)

                    if config.has_option(section, artifact + '_command'):
                        file_based = False
                        command = config.get(section, artifact + '_command')

                    if config.has_option(section, artifact + '_cleanup'):
                        tmp = config.get(section, artifact + '_cleanup')

                        if tmp.lower() == 'true':
                            cleanup = True
                        elif tmp.lower() == 'false':
                            cleanup = False
                        else:
                            raise RuntimeError("Invalid option for cleanup in client '%s', artifact '%s'" % (section, artifact))

                    if config.has_option(section, artifact + '_versions'):
                        try:
                            version = int(config.get(section, artifact + '_versions'))
                        except:
                            raise RuntimeError("Version option must be an integer in client '%s', artifact '%s'" % (section, artifact))

                    if config.has_option(section, artifact + '_interval'):
                        try:
                            interval = int(config.get(section, artifact + '_interval'))
                        except:
                            raise RuntimeError("Interval option must be an integer in client '%s', artifact '%s'" % (section, artifact))

                    artifacts[artifact] = {
                        'file_based': file_based,
                        'filename': filename,
                        'command': command,
                        'cleanup': cleanup,
                        'versions': versions,
                        'interval': interval
                    }

                self._clients[section] = artifacts

        if not len(self._clients) > 0:
            raise RuntimeError('No clients specified')

        self._server = None

    def run(self):
        logging.debug('Starting XMLRPC server')

        self._server = DocXMLRPCServer(("localhost", 8000), logRequests=False)
        self._server.register_instance(_XMLRPCServer(self._clients))
        self._server.serve_forever()

    def stop(self):
        logging.debug('Stopping XMLRPC Server')

        if self._server != None:
            self._server.shutdown()


class _XMLRPCServer(object):
    def __init__(self, clients):
        self._clients = clients

    def get_artifacts(self, client):
        return self._clients[client]

    def store_version(self, client, artifact, data):
        pass

    def get_version(self, client, artifact, version):
        pass

    def list_versions(self, client, artifact):
        pass