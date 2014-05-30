# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, time
import envoy, redis, rq
from usep_gh_handler_app.utils import logger_setup


class ProcessorUtils( object ):
    """ Supports processing. """

    def __init__( self, log ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.log = log

    ## handler web-app helpers ##

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
        files_to_process = { u'to_copy': [], u'to_remove': [], u'timestamp': unicode(datetime.datetime.now()) }
        if flask_request_data:
            commit_info = json.loads( flask_request_data )
            files_to_process[u'to_copy'] = commit_info[u'commits'][u'added']
            files_to_process[u'to_copy'].extend( commit_info[u'commits'][u'modified'] )
            files_to_process[u'to_remove'] = commit_info[u'commits'][u'removed']
        return files_to_process

    ## git pull ##

    def call_git_pull( self ):
        """ Runs git_pull.
                Returns list of filenames.
            Called by run_call_git_pull(). """
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

    ## files_to_process

    def get_files_to_copy( self, files_to_process ):
        """ Creates and returns list of filepaths to copy. """
        if files_to_process[u'to_copy'] == [ u'all' ]:
            filepaths_to_copy = self.make_complete_files_to_copy_list()  # TODO
        else:
            filepaths_to_copy = files_to_process[u'to_copy']
        self.log.debug( u'in utils.Processor.get_files_to_copy(); filepaths_to_copy, `%s`' % filepaths_to_copy )
        return filepaths_to_copy

    def get_files_to_remove( self, files_to_process ):
        """ Creates and returns list of filepaths to remove. """
        if files_to_process[u'to_remove'] == [ u'check' ]:
            filepaths_to_remove = self.make_complete_files_to_remove_list()  # TODO
        else:
            filepaths_to_remove = files_to_process[u'to_remove']
        self.log.debug( u'in utils.Processor.get_files_to_remove(); filepaths_to_remove, `%s`' % filepaths_to_remove )
        return filepaths_to_remove

    ## end class ProcessorUtils()


# class Processor( object ):
#     """


## queue runners ##

q = rq.Queue( u'usep', connection=redis.Redis() )

def run_call_git_pull( files_to_process ):
    """ Initiates a git pull update.
            Spawns a call to Processor.process_file() for each result found.
        Called by usep_gh_handler.handle_github_push(). """
    log = logger_setup.setup_logger()
    assert sorted( files_to_process.keys() ) == [ u'timestamp', u'to_copy', u'to_remove' ]; log.debug( u'in processor.run_call_git_pull(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
    time.sleep( 2 )  # let any existing jobs in process finish
    processor_utils = ProcessorUtils( log )
    processor_utils.call_git_pull()
    ( files_to_copy, files_to_remove ) = ( processor_utils.get_files_to_copy(files_to_process), processor_utils.get_files_to_remove(files_to_process) )
    for filepath in files_to_copy:
        job = q.enqueue_call( func=u'usep_gh_handler_app.utils.processor.run_copy_file', kwargs = {u'filepath': filepath} )
    for filepath in files_to_remove:
        job = q.enqueue_call( func=u'usep_gh_handler_app.utils.processor.run_remove_file', kwargs = {u'filepath': filepath} )
    return

# def run_call_git_pull( files_to_process ):
#     """ Initiates a git pull update.
#             Spawns a call to Processor.process_file() for each result found.
#         Called by usep_gh_handler.handle_github_push(). """
#     assert sorted( files_to_process.keys() ) == [ u'timestamp', u'to_copy', u'to_remove' ], sorted( github_file_info.keys() )
#     time.sleep( 2 )  # let any existing jobs in process finish
#     log = logger_setup.setup_logger()
#     log.debug( u'in processor.run_call_git_pull(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
#     processor_utils = ProcessorUtils( log )
#     processor_utils.call_git_pull()
#     # job = q.enqueue_call(
#     #     func=u'usep_gh_handler_app.utils.xyz',
#     #     kwargs = {} )
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
