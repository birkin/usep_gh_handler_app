# -*- coding: utf-8 -*-

import datetime, json, os, pprint
import flask, redis, rq
from flask.ext.basicauth import BasicAuth  # http://flask-basicauth.readthedocs.org/en/latest/
from usep_gh_handler_app.utils import log_helper
from usep_gh_handler_app.utils.web_app_helper import WebAppHelper


## setup
app = flask.Flask(__name__)
log = log_helper.setup_logger()
log.debug( u'in usep_gh_handler; log initialized' )
app.config[u'BASIC_AUTH_USERNAME'] = unicode( os.environ.get(u'usep_gh__BASIC_AUTH_USERNAME') )
app.config[u'BASIC_AUTH_PASSWORD'] = unicode( os.environ.get(u'usep_gh__BASIC_AUTH_PASSWORD') )
basic_auth = BasicAuth(app)
app_helper = WebAppHelper( log )
q = rq.Queue( u'usep', connection=redis.Redis() )


@app.route( u'/', methods=[u'GET', u'POST'] )
@app.route( u'/force/', methods=[u'GET', u'POST'] )  # for testing
@basic_auth.required
def handle_github_push():
    """ Triggers queue jobs: github pull, file copy, and index updates.
        Called from github push webhook.
        TODO: remove GET, now used for testing. """
    app_helper.log_github_post( flask.request )
    if not flask.request.data and u'force' not in flask.request.path:
        message = u'no files to process'
    else:
        files_to_process = app_helper.prep_data_dict( flask.request.data )  # dict of lists; to_copy, to_remove
        q.enqueue_call (
            func=u'usep_gh_handler_app.utils.processor.run_call_git_pull',
            kwargs = {u'files_to_process': files_to_process} )
        message = u'git pull initiated'
    log.debug( u'in usep_gh_handler.handle_github_push(); message, `%s`' % message )
    return u'received', 200
