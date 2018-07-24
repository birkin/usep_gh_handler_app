# -*- coding: utf-8 -*-

""" Handles log setup. """

import datetime, json, logging, os


LOG_CONF_JSN = os.environ['usep_gh__WRKR_LOG_CONF_JSN']
log = logging.getLogger( 'usep_gh_worker_logger' )
if not logging._handlers:  # true when module accessed by queue-jobs
    logging_config_dct = json.loads( LOG_CONF_JSN )
    logging.config.dictConfig( logging_config_dct )


def log_envoy_output( envoy_response ):
    """ Creates and returns dict of envoy_response attributes.
        Called by utils.processor.Puller.call_git_pull(). """
    log.debug( 'starting log_envoy_output()' )
    return_dict = {
        'status_code': envoy_response.status_code,  # int
        'std_out': envoy_response.std_out,
        'std_err': envoy_response.std_err,
        'command': envoy_response.command,  # list
        'history': envoy_response.history  # list
        }
    log.info( 'envoy_output, ```%s```' % return_dict )
    return return_dict
