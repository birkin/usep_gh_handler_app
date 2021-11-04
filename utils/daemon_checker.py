import logging, os, subprocess


log = logging.getLogger( 'usep_gh_web_logger' )
if not logging._handlers:  # true when module accessed by queue-jobs
    logging_config_dct = json.loads( LOG_CONF_JSN )
    logging.config.dictConfig( logging_config_dct )


def bar():
    return 'foo'


def check_daemon():
    """ Returns commit-string.
        Called by usep_gh_handler.daemon_check() """
    log.debug( 'starting check_daemon()' )
    ( check_result, err ) = ( 'not_found', '' )
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
            check_result = 'found'

    return ( check_result, err )

