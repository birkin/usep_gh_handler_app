# -*- coding: utf-8 -*-

""" Handles log setup. """

import logging, os
import logging.handlers

LOG_DIR = unicode( os.environ.get(u'usep_gh__LOG_DIR') )
LOG_LEVEL = unicode( os.environ.get(u'usep_gh__LOG_LEVEL') )


def setup_logger():
    """ Returns a logger to write to a file. """
    filename = u'%s/useh_gh_handler.log' % LOG_DIR
    formatter = logging.Formatter( u'[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s' )
    logger = logging.getLogger( u'usep_gh_handler' )
    level_dict = { u'debug': logging.DEBUG, u'info':logging.INFO }
    logger.setLevel( level_dict[LOG_LEVEL] )
    file_handler = logging.handlers.RotatingFileHandler( filename, maxBytes=(5*1024*1024), backupCount=1 )
    file_handler.setFormatter( formatter )
    logger.addHandler( file_handler )
    return logger
