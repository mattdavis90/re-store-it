import logging
import re
import os
from DocXMLRPCServer import DocXMLRPCServer
from DocXMLRPCServer import DocXMLRPCRequestHandler

from mode import Mode
from helper import get_config


class Server(Mode):
    def _initialise(self, args):
        logging.debug('Starting server mode checks on config file')
        
        config = get_config(args.config_file)

        self._clients = {}

        self._backup_location = ''
        self._port = 9001

        if config.has_option('server', 'backup_location'):
            self._backup_location = config.get('server', 'backup_location')

            if not os.path.isdir(self._backup_location):
                logging.warn("Backup location '%s' does not exist, attempting to create it" % self._backup_location)

                try:
                    os.makedirs(self._backup_location)
                except:
                    raise RuntimeError('Could not create the requested backup location')
        else:
            raise RuntimeError('Backup location not specified in config file')

        if not config.has_option('server', 'port'):
            logging.warn('No port specified, using 9001')
        else:
            try:
                self._port = int(config.get('server', 'port'))
            except:
                raise RuntimeError('Server port must be an integer')

        for section in config.sections():
            if not section == 'server':
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
                    backup_command = ''
                    restore_command = ''
                    cleanup = False
                    versions = 1
                    interval = '1h'

                    if config.has_option(section, artifact + '_filename'):
                        filename = config.get(section, artifact + '_filename')
                    else:
                        raise RuntimeError("Artifacts must have at least a file specified. Error in client '%s'" % section)

                    if config.has_option(section, artifact + '_backup_command'):
                        file_based = False
                        backup_command = config.get(section, artifact + '_backup_command')

                        if config.has_option(section, artifact + '_restore_command'):
                            restore_command = config.get(section, artifact + '_restore_command')
                        else:
                            raise RuntimeError("A backup command was specified without a restore command. A restore command is required in client '%s', artifact '%s'" % (section, artifact))

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
                            versions = int(config.get(section, artifact + '_versions'))
                        except:
                            raise RuntimeError("Version option must be an integer in client '%s', artifact '%s'" % (section, artifact))

                    if config.has_option(section, artifact + '_interval'):
                        interval = config.get(section, artifact + '_interval')
                        regex = "^(\d+w ?)?(\d+d ?)?(\d+h ?)?(\d+m ?)?(\d+s ?)?$"

                        if not re.search(regex, interval):
                            raise RuntimeError("Interval option must in valid timedelta format. e.g. 1w2d3h4m. In client '%s', artifact '%s'" % (section, artifact))

                    artifacts[artifact] = {
                        'file_based': file_based,
                        'filename': filename,
                        'backup_command': backup_command,
                        'restore_command': restore_command,
                        'cleanup': cleanup,
                        'versions': versions,
                        'interval': interval
                    }

                self._clients[section] = artifacts

        if not len(self._clients) > 0:
            raise RuntimeError('No clients specified')

        self._server = None

    def _add_arguments(self):
        self._parser.add_argument('config_file', metavar='CONFIGFILE')

    def run(self):
        logging.debug('Starting XMLRPC server')

        self._server = DocXMLRPCServer(('0.0.0.0', self._port), logRequests=False)
        self._server.register_instance(_XMLRPCServer(self._clients, self._backup_location))
        self._server.serve_forever()

    def stop(self):
        logging.debug('Stopping XMLRPC Server')

        if self._server != None:
            self._server.shutdown()


class _XMLRPCServer(object):
    def __init__(self, clients, backup_location):
        self._clients = clients
        self._backup_location = backup_location

    def get_artifacts(self, client):
        logging.info('Client %s - Requested artifacts' % client)

        return self._clients.get(client, {})

    def store_version(self, client, artifact, binary):
        if not self._clients.get(client):
            raise

        no_versions = self._clients[client][artifact]['versions']
         
        backup_path = os.path.join(self._backup_location, client, artifact)

        if not os.path.isdir(backup_path):
            logging.warn("Client %s - Artifact %s - directory doesn't exist, attempting to create" % (client, artifact))
            
            try:
                os.makedirs(backup_path)
            except:
                logging.error('Client %s - Artifact %s - Could not create directory')

                raise RuntimeError('Could not create backup directory for %s artifact %s' % (client, artifact))

        backup_file = os.path.join(backup_path, 'version0')

        versions = self.get_versions(client, artifact)

        if len(versions) >= no_versions:
            logging.debug('Client %s - Artifact %s - Removing old version' % (client, artifact))

            os.unlink(versions[-1]['filepath'])
            
            del versions[-1]

        if len(versions) > 0:
            for i in range(len(versions) - 1, -1, -1):
                old_name = versions[i]['filename']
                new_name = 'version%d' % (int(re.match('^.*(\d+)$', old_name).group(1)) + 1)

                old_path = os.path.join(backup_path, old_name)
                new_path = os.path.join(backup_path, new_name)

                os.rename(old_path, new_path)

        with open(backup_file, 'wb') as handle:
            handle.write(binary.data)

        logging.info('Client %s - Artifact %s - Stored new version' % (client, artifact))

        return True
        
    def get_version(self, client, artifact, version):
        pass

    def get_versions(self, client, artifact):
        backup_path = os.path.join(self._backup_location, client, artifact)

        versions = []

        if os.path.isdir(backup_path):
            backup_list = os.listdir(backup_path)

            for backup in backup_list:
                file_path = os.path.join(backup_path, backup)
                modified = os.stat(file_path).st_mtime

                versions.append({'filename': backup, 'filepath': file_path, 'modified': modified})

            versions.sort(key=lambda itm: itm['modified'], reverse=True)

        return versions