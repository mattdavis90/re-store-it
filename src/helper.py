import os
import ConfigParser
import logging
import xmlrpclib


def get_config(config_file):
    if not os.path.exists(config_file):
        logging.error('Config file not found')
        sys.exit(1)

    config = ConfigParser.ConfigParser()
    
    logging.debug('Loading config file')

    config.readfp(open(config_file))

    return config

def wrap_xmlrpc(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except xmlrpclib.Error as err:
        logging.error('There was an XMLRPC error: %s' % err)
    except Exception:
        logging.error('Unable to connect to XMLRPC server')

    return None