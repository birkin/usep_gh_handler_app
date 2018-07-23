# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, sys
import flask, redis, requests, rq
from flask_basicauth import BasicAuth  # http://flask-basicauth.readthedocs.org/en/latest/

## update sys.path
cwd_parent = os.path.dirname( os.getcwd() )
if cwd_parent not in sys.path:
    sys.path.append( cwd_parent )

## rest of imports
from usep_gh_handler_app.utils.web_app_helper import WebAppHelper

## setup
B_AUTH_PASSWORD = os.environ[u'usep_gh__BASIC_AUTH_PASSWORD']
B_AUTH_USERNAME = os.environ[u'usep_gh__BASIC_AUTH_USERNAME']
LOG_CONF_JSN = os.environ[u'usep_gh__LOG_CONF_JSN']

logging_config_dct = json.loads( LOG_CONF_JSN )
log = logging.getLogger( 'usep_gh_web_logger' )
logging.config.dictConfig( logging_config_dct )
log.debug( 'logging ready' )

app = flask.Flask(__name__)
app.config[u'BASIC_AUTH_USERNAME'] = B_AUTH_USERNAME
app.config[u'BASIC_AUTH_PASSWORD'] = B_AUTH_PASSWORD
app.config[u'JSONIFY_PRETTYPRINT_REGULAR'] = True
basic_auth = BasicAuth(app)
app_helper = WebAppHelper()
q = rq.Queue( u'usep', connection=redis.Redis() )


@app.route( u'/info/', methods=[u'GET'] )
def info():
    log.debug( 'in info()' )
    dct = {
        u'datetime': str( datetime.datetime.now() ),
        u'info': u'https://github.com/Brown-University-Library/usep_gh_handler_app'
    }
    return flask.jsonify( dct )


@app.route( u'/reindex_all/', methods=[u'GET'] )
@basic_auth.required
def reindex_all():
    """ Triggers a git-pull and a re-index of everything.
        Called via admin. """
    try:
        log.debug( u'in usep_gh_handler.reindex_all(); starting' )
        q.enqueue_call (
            func=u'usep_gh_handler_app.utils.reindex_all_support.run_call_simple_git_pull',
            kwargs = {} )
        return u'pull and reindex initiated.', 200
    except Exception as e:
        log.error( u'in usep_gh_handler.reindex_all(); error, `%s`' % unicode(repr(e)) )


@app.route( u'/', methods=[u'GET', u'POST'] )
@app.route( u'/force/', methods=[u'GET', u'POST'] )  # for testing
@basic_auth.required
def handle_github_push():
    """ Triggers queue jobs: github pull, file copy, and index updates.
        Called from github push webhook.
        TODO: remove GET, now used for testing. """
    try:
        log.debug( u'starting (basic-auth successful)' )
        app_helper.log_github_post( flask.request )
        # app_helper.trigger_dev_if_production( flask.request.host )  # github can only hit production; we want dev updated, too -- temporarily disabled
        log.debug( u'checked trigger-dev step' )
        log.debug( u'flask.request.data, ```%s```' % flask.request.data )
        if flask.request.data or u'force' in flask.request.path:
            log.debug( 'going to check for files_to_process' )
            files_to_process = app_helper.prep_data_dict( flask.request.data )  # returns dict of lists; files_updated, files_removed
            log.debug( 'about to enqueue job; files_to_process, ```{}```'.format( pprint.pformat(files_to_process) ) )
            q.enqueue_call (
                func=u'usep_gh_handler_app.utils.processor.run_call_git_pull',
                kwargs = {u'files_to_process': files_to_process} )
            log.debug( u'job enqueued' )
        log.debug( u'returning 200' )
        return u'received', 200
    except Exception as e:
        log.error( u'error, `%s`' % unicode(repr(e)) )
