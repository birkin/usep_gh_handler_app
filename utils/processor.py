# -*- coding: utf-8 -*-

import logging, os, pprint
import envoy, redis, rq


log = logging.getLogger(__name__)


class ProcessorUtils( object ):
    """ Handles the git-pull command, parses results, and returns list of filenames. """

    def __init__( self, log ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.log = log

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
        self.log.info( u'in utils.Processor._examine_command_output(); envoy_output, `%s`' % return_dict )
        return return_dict

    ## end class ProcessorUtils()


# class Processor( object ):
#     """


## queue runners ##

q = rq.Queue( u'usep', connection=redis.Redis() )

def run_call_git_pull():
    """ Initiates a git pull update.
            Spawns a call to Processor.process_file() for each result found.
        Called by usep_gh_handler.handle_github_push(). """
    processor_utils = ProcessorUtils( log )
    processor_utils.call_git_pull()
    job = q.enqueue_call(
        func=u'usep_gh_handler_app.utils.xyz',
        kwargs = {} )
    return

def run_process_inscription( kwargs ):
    """ Stub; TODO, build out.
        Moves inscription to correct place, and indexes it.
        Called by queue-job created by processor.py run_call_git_pull(). """
    filename = kwargs[u'filename']
    processor = Processor()
    processor.move_file( filename )
    processor.index_file( filename )
    return
