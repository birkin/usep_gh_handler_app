# -*- coding: utf-8 -*-

""" Handles log setup. """

import datetime, logging, os


def setup_logger():
    """ Returns a logger to write to a file.
        Called by usep_gh_handler.py and processor.py functions. """
    LOG_DIR = unicode( os.environ.get(u'usep_gh__LOG_DIR') )
    LOG_LEVEL = unicode( os.environ.get(u'usep_gh__LOG_LEVEL') )
    filename = u'%s/usep_gh_handler.log' % LOG_DIR
    formatter = logging.Formatter( u'[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s' )
    logger = logging.getLogger( __name__ )
    # logger = logging.getLogger( u'usep_gh_handler' )
    level_dict = { u'debug': logging.DEBUG, u'info':logging.INFO }
    logger.setLevel( level_dict[LOG_LEVEL] )
    file_handler = logging.FileHandler( filename )
    file_handler.setFormatter( formatter )
    logger.addHandler( file_handler )
    logger.debug( u'in utils.log_helper.setup_logger(); log initialized at %s' % unicode(datetime.datetime.now()) )
    return logger


def log_envoy_output( log, envoy_response ):
    """ Creates and returns dict of envoy_response attributes.
        Called by utils.processor.Puller.call_git_pull(). """
    return_dict = {
        u'status_code': envoy_response.status_code,  # int
        u'std_out': envoy_response.std_out.decode(u'utf-8'),
        u'std_err': envoy_response.std_err.decode(u'utf-8'),
        u'command': envoy_response.command,  # list
        u'history': envoy_response.history  # list
        }
    log.info( u'in utils.log_helper.log_envoy_output(); envoy_output, `%s`' % return_dict )
    return return_dict
