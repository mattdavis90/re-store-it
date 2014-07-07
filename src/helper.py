import os
import ConfigParser
import logging
import re
import xmlrpclib


def get_config(config_file):
    if not os.path.exists(config_file):
        logging.error('Config file not found')
        sys.exit(1)

    config = ConfigParser.ConfigParser()
    
    logging.debug('Loading config file')

    config.readfp(open(config_file))

    return config

def get_server_url(config):
    if not config.has_section('client'):
        raise RuntimeError("Config file requires a 'client' section")

    if not config.has_option('client', 'server'):
        raise RuntimeError('Server not specified in config file')

    server_url = config.get('client', 'server')

    regex = '^http://.*:\d+/$'

    if not re.search(regex, server_url):
        raise RuntimeError('Server should be in the format http://127.0.0.1:9001/')

    return server_url

def wrap_xmlrpc(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except xmlrpclib.Error as err:
        logging.error('There was an XMLRPC error: %s' % err)
    except Exception:
        logging.error('Unable to connect to XMLRPC server')

    return None