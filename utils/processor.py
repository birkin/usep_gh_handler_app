# -*- coding: utf-8 -*-

import logging, os, pprint
import envoy


log = logging.getLogger(__name__)


class ProcessorUtils( object ):
    """ Container for support-tasks for processing inscriptions. """

    def __init__( self ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )

    def call_git_pull( self ):
        """ Runs git_pull.
                Returns list of filenames.
            Called by (eventually) a github-trigger, and an admin-trigger. """
        ## change to the target directory
        return_directory = os.getcwd()
        os.chdir( self.GIT_CLONED_DIR_PATH )
        ## call git pull
        command = u'git pull'
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        ( std_out, std_err ) = ( r.std_out.decode(u'utf-8'), r.std_err.decode(u'utf-8') )
        log.info( 'in processor.call_git_pull(); std_out, `%s`; std_err, `%s`' % (std_out, std_err) )
        return
        # result_dict = self.parse_update_output( std_out )
        # return {
        #     u'status_code': r.status_code,
        #     u'std_out': std_out,
        #     u'std_err': r.std_err.decode(u'utf-8'),
        #     u'command': r.command,
        #     u'history': r.history,
        #     u'file_ids': result_dict[u'file_ids'] }

    def parse_update_output( self, std_out ):
        """ Takes envoy stdout string.
                Tries to create file_ids list.
                Returns file list.
            Called by self.run_svn_update(). """
        assert type(std_out) == unicode
        file_ids = []
        lines = std_out.split()
        for line in lines:
            if u'.xml' in line:
                segments = line.split( u'/' )
                file_ids.append( segments[-1][:-4] )  # last segment is abc.xml; file_id is all but last 4 characters
        return { u'file_ids': sorted(file_ids) }

    ## end class ProcessorUtils()
