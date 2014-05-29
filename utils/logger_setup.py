# -*- coding: utf-8 -*-

""" Handles log setup. """

import logging, os
# import logging.handlers


def setup_logger():
    """ Returns a logger to write to a file. """
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
    return logger
