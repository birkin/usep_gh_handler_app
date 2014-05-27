# -*- coding: utf-8 -*-

import datetime, json, os, pprint
import flask, redis, rq
from flask.ext.basicauth import BasicAuth  # http://flask-basicauth.readthedocs.org/en/latest/
from usep_gh_handler_app.utils import logger_setup
from usep_gh_handler_app.utils.processor import ProcessorUtils


## setup
app = flask.Flask(__name__)
log = logger_setup.setup_logger()
log.debug( u'in usep_gh_handler; log initialized' )
app.config[u'BASIC_AUTH_USERNAME'] = unicode( os.environ.get(u'usep_gh__BASIC_AUTH_USERNAME') )
app.config[u'BASIC_AUTH_PASSWORD'] = unicode( os.environ.get(u'usep_gh__BASIC_AUTH_PASSWORD') )
basic_auth = BasicAuth(app)
processor_utils = ProcessorUtils( log )
q = rq.Queue( u'usep', connection=redis.Redis() )


@app.route( u'/', methods=[u'GET', u'POST'] )
@basic_auth.required
def handle_github_push():
    """ Triggers queue jobs: github pull, file copy, and index updates.
        Called from github push webhook.
        TODO: remove GET, now used for testing. """
    processor_utils.log_github_post( flask.request )
    if not flask.request.data:
        message = u'no files to process'
    else:
        data = processor_utils.prep_data_dict( flask.request.data )
        q.enqueue_call (
            func=u'usep_gh_handler_app.utils.processor.run_call_git_pull',
            kwargs = {u'github_file_info': data} )
        message = u'git pull initiated'
    log.debug( u'in usep_gh_handler.handle_github_push(); message, `%s`' % message )
    return u'received', 200




if __name__ == u'__main__':
    if os.getenv(u'DEVBOX') == u'true':
        app.run( host=u'0.0.0.0', debug=True )
    else:
        app.run()
