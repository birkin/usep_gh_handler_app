# -*- coding: utf-8 -*-

import datetime, json, os, pprint
import flask, redis, rq
from usep_gh_handler_app.utils import logger_setup


## setup
app = flask.Flask(__name__)
log = logger_setup.setup_logger()
log.debug( u'in usep_gh_handler; log initialized' )
LEGIT_IPS = json.loads( unicode(os.environ.get(u'usep_gh__LEGIT_IPS')) )


@app.route( u'/', methods=[u'GET', u'POST'] )
# @basic_auth.required
def handle_github_push():
    """ Triggers github pull.
        Called from github push webhook.
        TODO: remove GET, now used for testing. """
    if not _validate_ip( flask.request.remote_addr ) == u'valid':
        return flask.abort( 403 )
    q = rq.Queue( u'usep', connection=redis.Redis() )
    q.enqueue_call (
        func=u'usep_gh_handler_app.utils.run_call_github_pull',
        kwargs = {} )
    log.debug( u'in usep_gh_handler.handle_github_push(); job enqueued fine' )
    return_dict = {
        u'datetime': datetime.datetime.now(),
        u'response': u'git pull initiated' }
    return flask.jsonify( return_dict )

def _validate_ip( client_ip ):
    """ Logs and validates ip.
        Returns 'valid' or 'invalid'.
        Called by handle_github_push(). """
    log.info( u'in usep_gh_handler._validate_ip(); client_ip, `%s`' % client_ip )
    if client_ip in LEGIT_IPS.keys():
        validity = u'valid'
    else:
        log.info( u'in usep_gh_handler.handle_github_push(); client_ip not in LEGIT_IPS; will return forbidden' )
        validity = u'invalid'
    return validity




if __name__ == '__main__':
    if os.getenv('DEVBOX') == 'true':
        app.run( host='0.0.0.0', debug=True )
    else:
        app.run()
