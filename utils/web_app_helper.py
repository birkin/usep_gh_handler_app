# -*- coding: utf-8 -*-

import datetime, pprint
import flask
# from usep_gh_handler_app.utils import log_helper


class WebAppHelper( object ):
    """ Contains support functions for usep_gh_handler.py """

    def __init__( self, log ):
        """ Settings. """
        self.log = log

    def log_github_post( self, flask_request ):
        """ Logs data posted from github.
            Called by usep_gh_handler.handle_github_push() """
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
        files_to_process = { u'files_updated': [], u'files_removed': [], u'timestamp': unicode(datetime.datetime.now()) }
        if flask_request_data:
            commit_info = json.loads( flask_request_data )
            ( added, modified, removed ) = self._examine_commits( commit_info )
            files_to_process[u'files_updated'] = added
            files_to_process[u'files_updated'].extend( modified )  # solrization same for added or modified
            files_to_process[u'files_removed'] = removed
        self.log.debug( u'in processor.prep_data_dict(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
        return files_to_process

    def _examine_commits( self, commit_info ):
        """ Extracts and returns file-paths for the different kinds of commits.
            Called by prep_data_dict(). """
        added = []
        modified = []
        removed = []
        for commit in commit_info[u'commits']:
            added.extend( commit[u'added'] )
            modified.extend( commit[u'modified'] )
            removed.extend( commit[u'removed'] )
        return ( added, modified, removed )

    ## end class WebAppHelper()
