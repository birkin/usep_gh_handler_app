# -*- coding: utf-8 -*-

import datetime, json, os, pprint
import flask, redis, rq
from usep_gh_handler_app.utils import logger_setup
from flask.ext.basicauth import BasicAuth  # http://flask-basicauth.readthedocs.org/en/latest/


## setup
app = flask.Flask(__name__)
log = logger_setup.setup_logger()
log.debug( u'in usep_gh_handler; log initialized' )
app.config['BASIC_AUTH_USERNAME'] = unicode( os.environ.get(u'usep_gh__BASIC_AUTH_USERNAME') )
app.config['BASIC_AUTH_PASSWORD'] = unicode( os.environ.get(u'usep_gh__BASIC_AUTH_PASSWORD') )
basic_auth = BasicAuth(app)


@app.route( u'/', methods=[u'GET', u'POST'] )
@basic_auth.required
def handle_github_push():
    """ Triggers queue jobs: github pull, file copy, and index updates.
        Called from github push webhook.
        TODO: remove GET, now used for testing. """
    # q = rq.Queue( u'usep', connection=redis.Redis() )
    # q.enqueue_call (
    #     func=u'usep_gh_handler_app.utils.processor.run_call_git_pull',
    #     kwargs = {} )
    # log.debug( u'in usep_gh_handler.handle_github_push(); job enqueued fine' )
    return_dict = {}
    return_dict = {
        u'datetime': datetime.datetime.now(),
        u'args': flask.request.args,
        u'cookies': flask.request.cookies,
        u'data': flask.request.data,
        u'form': flask.request.form,
        u'headers': unicode(repr(flask.request.headers)),
        u'method': flask.request.method,
        u'path': flask.request.path,
        u'remote_addr': flask.request.remote_addr,
        u'values': flask.request.values,
        }
    log.debug( u'in usep_gh_handler.handle_github_push(); return_dict, `%s`' % pprint.pformat(return_dict) )
    return flask.jsonify( return_dict )




if __name__ == '__main__':
    if os.getenv('DEVBOX') == 'true':
        app.run( host='0.0.0.0', debug=True )
    else:
        app.run()
