# -*- coding: utf-8 -*-

from __future__ import unicode_literals


import datetime, json, logging, os, pprint, secrets, sys

import flask, redis, requests, rq
from flask_basicauth import BasicAuth  # http://flask-basicauth.readthedocs.org/en/latest/

## update sys.path
cwd_parent = os.path.dirname( os.getcwd() )
if cwd_parent not in sys.path:
    sys.path.append( cwd_parent )

## rest of imports
from usep_gh_handler_app.utils.web_app_helper import WebAppHelper
from usep_gh_handler_app.utils.orphan_manager import OrphanDeleter

## setup
B_AUTH_PASSWORD = os.environ['usep_gh__BASIC_AUTH_PASSWORD']
B_AUTH_USERNAME = os.environ['usep_gh__BASIC_AUTH_USERNAME']
LOG_CONF_JSN = os.environ['usep_gh__LOG_CONF_JSN']
SOLR_URL = os.environ['usep_gh__SOLR_URL']

logging_config_dct = json.loads( LOG_CONF_JSN )
log = logging.getLogger( 'usep_gh_web_logger' )
logging.config.dictConfig( logging_config_dct )
log.debug( 'logging ready' )

app = flask.Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = B_AUTH_USERNAME
app.config['BASIC_AUTH_PASSWORD'] = B_AUTH_PASSWORD
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
tkn = secrets.token_urlsafe( 16 )
app.config["SECRET_KEY"] = tkn

basic_auth = BasicAuth(app)
app_helper = WebAppHelper()
orphan_manager = OrphanDeleter()
q = rq.Queue( 'usep', connection=redis.Redis() )


@app.route( '/info/', methods=['GET'] )
def info():
    log.debug( 'in info()' )
    dct = {
        'datetime': str( datetime.datetime.now() ),
        'info': 'https://github.com/Brown-University-Library/usep_gh_handler_app'
    }
    return flask.jsonify( dct )


@app.route( '/list_orphans/', methods=['GET'] )
@basic_auth.required
def list_orphans():
    """ Builds list of active inscription_ids, builds list of solr inscription_ids, presents results.
        Called via admin. """
    log.debug( '\n\nstarting list_orphans()' )
    orphan_handler_url = flask.url_for('delete_orphans')
    log.debug( f'orphan_handler url, ```{orphan_handler_url}```' )
    start_time = datetime.datetime.now()
    flask.session['ids_to_delete'] = json.dumps( [] )
    data = orphan_manager.prep_orphan_list()
    flask.session['ids_to_delete'] = json.dumps( data )
    context = orphan_manager.prep_context( data, orphan_handler_url, start_time )
    log.debug( f'context, ```{pprint.pformat(context)}```' )
    if flask.request.args.get('format') == 'json':
        return flask.jsonify( context )
    else:
        html = orphan_manager.build_html( context )
        return html, 200


@app.route( '/orphan_handler/', methods=['GET'] )
@basic_auth.required
def delete_orphans():
    """ Runs orphan-delete if necessary.
        Called via admin. """
    log.debug( '\n\nstarting delete_orphans()' )
    # log.debug( f'request, ```{pprint.pformat(flask.request.__dict__)}```' )

    start_time = datetime.datetime.now()
    ids_to_delete = flask.session['ids_to_delete']
    log.debug( f'ids_to_delete, ```{pprint.pformat(ids_to_delete)}```' )

    errors = []
    for delete_id in ids_to_delete:
        try:
            s = solr.Solr( self.SOLR_URL )
            time.sleep( .5 )
            response = s.delete( id=delete_id )
            s.commit()
            s.close()
            log.debug( f'id, ```{delete_id}```; response, ```{response}```' )
            break
        except:
            errors.append( delete_id )
            log.traceback( f'error trying to delete id, ```{delete_id}```; processing will continue after traceback...' )

    if errors == []:
        return 'all orphans deleted', 200
    else:
        return 'problems deleting some orphans; see logs for details'

@app.route( '/reindex_all/', methods=['GET'] )
@basic_auth.required
def reindex_all():
    """ Triggers a git-pull and a re-index of everything.
        Called via admin. """
    try:
        log.debug( 'in usep_gh_handler.reindex_all(); starting' )
        q.enqueue_call (
            func='usep_gh_handler_app.utils.reindex_all_support.run_call_simple_git_pull',
            kwargs = {} )
        return 'pull and reindex initiated.', 200
    except Exception as e:
        log.error( 'in usep_gh_handler.reindex_all(); error, `%s`' % e )


@app.route( '/', methods=['GET', 'POST'] )
@app.route( '/force/', methods=['GET', 'POST'] )  # for testing
@basic_auth.required
def handle_github_push():
    """ Triggers queue jobs: github pull, file copy, and index updates.
        Called from github push webhook.
        TODO: remove GET, now used for testing. """
    try:
        log.debug( 'starting (basic-auth successful)' )
        app_helper.log_github_post( flask.request )
        # app_helper.trigger_dev_if_production( flask.request.host )  # github can only hit production; we want dev updated, too -- temporarily disabled
        log.debug( 'checked trigger-dev step' )
        log.debug( 'flask.request.data, ```%s```' % flask.request.data )
        if flask.request.data or 'force' in flask.request.path:
            log.debug( 'going to check for files_to_process' )
            files_to_process = app_helper.prep_data_dict( flask.request.data )  # returns dict of lists; files_updated, files_removed
            log.debug( 'about to enqueue job; files_to_process, ```{}```'.format( pprint.pformat(files_to_process) ) )
            q.enqueue_call (
                func='usep_gh_handler_app.utils.processor.run_call_git_pull',
                kwargs = {'files_to_process': files_to_process} )
            log.debug( 'job enqueued' )
        log.debug( 'returning 200' )
        return 'received', 200
    except Exception as e:
        log.error( 'error, `%s`' % e )
