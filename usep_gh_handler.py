# -*- coding: utf-8 -*-

import datetime, json, os, pprint
import flask, redis, rq
# from usep_gh_handler_app.config import settings
from usep_gh_handler_app.utils import logger_setup
# from flask.ext.basicauth import BasicAuth  # http://flask-basicauth.readthedocs.org/en/latest/


## setup
app = flask.Flask(__name__)
log = logger_setup.setup_logger()
log.debug( u'in usep_gh_handler; log initialized' )
#
# app.config['BASIC_AUTH_USERNAME'] = settings.BASIC_AUTH_USERNAME
# app.config['BASIC_AUTH_PASSWORD'] = settings.BASIC_AUTH_PASSWORD
# basic_auth = BasicAuth(app)

LEGIT_IPS = json.loads( unicode(os.environ.get(u'usep_gh__LEGIT_IPS')) )



@app.route( u'/', methods=[u'GET', u'POST'] )
# @basic_auth.required
def handle_github_push():
    """ Triggers github pull.
        Called from github push webhook.
        TODO: remove GET, now used for testing. """
    log.debug( u'in usep_gh_handler.handle_github_push(); starting' )
    ## validate ip
    client_ip = flask.request.remote_addr
    if not client_ip in LEGIT_IPS.keys():
        log.info( u'in usep_gh_handler.handle_github_push(); client_ip `%s` not in LEGIT_IPS; returning forbidden' % client_ip )
        return flask.abort( 403 )
    log.debug( u'in usep_gh_handler.handle_github_push(); client_ip must have been good' )
    ## kickoff job
    try:
        q = rq.Queue( u'usep', connection=redis.Redis() )
        log.debug( u'in usep_gh_handler.handle_github_push(); queue instantiation fine' )
    except Exception as e:
        log.error( u'in usep_gh_handler.handle_github_push(); exception on queue instantiation, `%s`' % unicode(repr(e)) )
    try:
        job = q.enqueue_call (
            func=u'usep_gh_handler_app.utils.run_call_github_pull',
            kwargs = {}
            )
        log.debug( u'in usep_gh_handler.handle_github_push(); job enqueued fine' )
    except Exception as e:
        log.error( u'in usep_gh_handler.handle_github_push(); exception on job-enqueue, `%s`' % unicode(repr(e)) )

    job_dict = job.__dict__
    log.debug( u'in usep_gh_handler.handle_github_push(); job.__dict__, `%s`' % pprint.pformat(job_dict) )
    ## respond (development-GET)
    if flask.request.method == u'GET':
        log.debug( u'in usep_gh_handler.handle_github_push(); request.method is GET' )
        try:
            return_dict = {
                u'request_type': u'manually triggered (not github)',
                u'datetime': unicode( datetime.datetime.now() ),
                u'job': pprint.pformat(job_dict) }
            log.debug( u'in usep_gh_handler.handle_github_push(); return_dict is fine' )
        except Exception as e:
            log.error( u'in usep_gh_handler.handle_github_push(); exception creating return_dict, `%s`' % unicode(repr(e)) )
        try:
            return flask.jsonify( return_dict )
        except Exception as e:
            log.error( u'in usep_gh_handler.handle_github_push(); exception on return, `%s`' % unicode(repr(e)) )





if __name__ == '__main__':
    if os.getenv('DEVBOX') == 'true':
        app.run( host='0.0.0.0', debug=True )
    else:
        app.run()
