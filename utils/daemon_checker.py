import json, logging, os, subprocess


log = logging.getLogger( 'usep_gh_web_logger' )
if not logging._handlers:  # true when module accessed by queue-jobs
    logging_config_dct = json.loads( LOG_CONF_JSN )
    logging.config.dictConfig( logging_config_dct )


def check_daemon():
    """ Returns commit-string.
        Called by usep_gh_handler.daemon_check() """
    log.debug( 'starting check_daemon()' )
    ( check_result, err ) = ( 'daemon_not_active', '' )
    try:
        output_utf8 = subprocess.check_output( ['ps', 'ax'], stderr=subprocess.STDOUT )
        assert type(output_utf8) == bytes
        output = output_utf8.decode( 'utf8' )
        assert type(output) == str
        log.debug( f'output, ``{output}``' )
    except Exception as e:
        err = repr( e )
        log.exception( f'problem running ps, ``{err}``' )
    if err == '':
        if 'rqworker usep' in output.lower():
            check_result = 'daemon_active'
    return ( check_result, err )


def validate_request_source( hostname ):
    """ Checks perceived hostname against legit-list.
        Called by usep_gh_handler.daemon_check() """
    log.debug( f'hosname, ``{hostname}``' )
    ( result, err ) = ( 'invalid', '' )
    try:
        legit_hostnames = json.loads( os.environ['usep_gh__LEGIT_HOSTNAMES_JSON'] )
        if hostname in legit_hostnames:
            result = 'valid'
        else:
            log.warning( f'perceived invalid hostname, ``{hostname}``; returning result, ``{result}``' )
    except Exception as e:
        err = repr( e )
        log.exception( f'Problem loading legit hostnames' )
    log.debug( f'result, ``{result}``' )
    log.debug( f'err, ``{err}``' )
    return ( result, err )

