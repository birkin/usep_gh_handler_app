# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, time
import envoy, redis, rq
from usep_gh_handler_app.utils import logger_setup


class ProcessorUtils( object ):
    """ Handles the git-pull command. """

    def __init__( self, log ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.log = log

    ## git pull ##

    def call_git_pull( self ):
        """ Runs git_pull.
                Returns list of filenames.
            Called by (eventually) a github-trigger, and an admin-trigger. """
        original_directory = os.getcwd()
        os.chdir( self.GIT_CLONED_DIR_PATH )
        command = u'git pull'
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        self._log_command_output( r )
        os.chdir( original_directory )
        return

    def _log_command_output( self, envoy_response ):
        """ Creates and returns dict of envoy_response attributes.
            Called by call_git_pull(). """
        return_dict = {
            u'status_code': envoy_response.status_code,  # int
            u'std_out': envoy_response.std_out.decode(u'utf-8'),
            u'std_err': envoy_response.std_err.decode(u'utf-8'),
            u'command': envoy_response.command,  # list
            u'history': envoy_response.history  # list
            }
        self.log.info( u'in utils.Processor._log_command_output(); envoy_output, `%s`' % return_dict )
        return return_dict

    ## handler-app helpers ##

    def log_github_post( self, flask_request ):
        """ Logs data posted from github.
            Called by usep_gh_handler.handle_github_push() """
        github_data_dict = {}
        github_data_dict = {
            u'datetime': datetime.datetime.now(),
            u'args': flask_request.args,
            u'cookies': flask_request.cookies,
            u'data': flask_request.data,
            u'form': flask_request.form,
            u'headers': unicode(repr(flask_request.headers)),
            u'method': flask_request.method,
            u'path': flask_request.path,
            u'remote_addr': flask_request.remote_addr,
            u'values': flask_request.values,
            }
        self.log.debug( u'in utils.processor.log_github_post(); github_data_dict, `%s`' % pprint.pformat(github_data_dict) )
        return

    def prep_data_dict( self, flask_request_data ):
        """ Prepares the data-dict to be sent to run_call_git_pull().
            Called by usep_gh_handler.handle_github_push() """
        self.log.debug( u'in processor.prep_data_dict(); flask_request_data, `%s`' % flask_request_data )
        data = { u'added': [], u'modified': [], u'removed': [], u'timestamp': unicode(datetime.datetime.now()) }
        if flask_request_data:
            commit_info = json.loads( flask_request_data )
            data[u'added'] = commit_info[u'commits'][u'added']
            data[u'modified'] = commit_info[u'commits'][u'modified']
            data[u'removed'] = commit_info[u'commits'][u'removed']
        return data

    ## end class ProcessorUtils()


# class Processor( object ):
#     """


## queue runners ##

q = rq.Queue( u'usep', connection=redis.Redis() )

def run_call_git_pull( github_file_info ):
    """ Initiates a git pull update.
            Spawns a call to Processor.process_file() for each result found.
        Called by usep_gh_handler.handle_github_push(). """
    print u'- HERE01'
    assert sorted( github_file_info.keys() ) == [ u'added', u'modified', u'removed', u'timestamp' ], sorted( github_file_info.keys() )
    time.sleep( 1 )  # let any existing jobs in process finish
    log = logger_setup.setup_logger()
    log.debug( u'in processor.run_call_git_pull(); github_file_info, `%s`' % pprint.pformat(github_file_info) )
    processor_utils = ProcessorUtils( log )
    processor_utils.call_git_pull()
    # job = q.enqueue_call(
    #     func=u'usep_gh_handler_app.utils.xyz',
    #     kwargs = {} )
    return

# def run_call_git_pull( data ):
#     """ Initiates a git pull update.
#             Spawns a call to Processor.process_file() for each result found.
#         Called by usep_gh_handler.handle_github_push(). """
#     assert sorted( data.keys() ) == [ u'added', u'deleted', u'modified', u'timestamp' ]
#     time.sleep( 5 )  # let any existing jobs in process finish
#     processor_utils = ProcessorUtils( log )
#     processor_utils.call_git_pull()
#     job = q.enqueue_call(
#         func=u'usep_gh_handler_app.utils.xyz',
#         kwargs = {} )
#     return

# def run_process_inscription( kwargs ):
#     """ Stub; TODO, build out.
#         Moves inscription to correct place, and indexes it.
#         Called by queue-job created by processor.py run_call_git_pull(). """
#     filename = kwargs[u'filename']
#     processor = Processor()
#     processor.move_file( filename )
#     processor.index_file( filename )
#     return
