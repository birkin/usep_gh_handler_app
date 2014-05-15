# -*- coding: utf-8 -*-

import logging, os, pprint
import envoy


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
        command_output = self._examine_command_output( r )
        filenames_list = self.parse_pull_output( command_output[u'std_out'] )
        os.chdir( original_directory )
        return filenames_list

    def parse_pull_output( self, std_out ):
        """ Takes envoy stdout string.
                Parses out filenames.
                Returns list.
            Called by self.run_svn_update(). """
        assert type(std_out) == unicode
        file_ids = []
        lines = std_out.split()
        for line in lines:
            if u'.xml' in line:
                segments = line.split( u'/' )
                file_ids.append( segments[-1][:-4] )  # last segment is abc.xml; file_id is all but last 4 characters
        return { u'file_ids': sorted(file_ids) }

    def _examine_command_output( self, envoy_response ):
        """ Creates and returns dict of envoy_response attributes.
            Called by call_git_pull(). """
        return_dict = {
            u'status_code': envoy_response.status_code.decode(u'utf-8'),
            u'std_out': envoy_response.std_out.decode(u'utf-8'),
            u'std_err': envoy_response.std_err.decode(u'utf-8'),
            u'command': envoy_response.command.decode(u'utf-8'),
            u'history': envoy_response.history.decode(u'utf-8')
            }
        self.log.info( u'in Processor._examine_command_output(); envoy_output, `%s`' % return_dict )
        return return_dict

    ## end class ProcessorUtils()


# class Processor( object ):
#     """


## queue runners ##

q = rq.Queue( u'iip', connection=redis.Redis() )

def run_call_git_pull():
    """ Initiates a git pull update.
            Spawns a call to Processor.process_file() for each result found.
        Called by usep_gh_handler.handle_github_push(). """
    processor_utils = ProcessorUtils( log )
    result_dict = processor_utils.call_git_pull()
    log.info( u'in processor.py run_call_git_pull(); result_dict is, ```%s```' % pprint.pformat(result_dict) )
    for filename in result_dict[u'filenames']:
        job = q.enqueue_call(
            func=u'usep_gh_handler_app.utils.run_process_inscription',
            kwargs = { u'filename': filename } )
    return

def run_process_inscription( kwargs ):
    """ Moves inscription to correct place, and indexes it.
        Called by queue-job created by processor.py run_call_git_pull(). """
    filename = kwargs[u'filename']
    processor = Processor()
    processor.move_file( filename )
    processor.index_file( filename )
    return
