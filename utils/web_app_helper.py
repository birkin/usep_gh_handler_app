# -*- coding: utf-8 -*-

from usep_gh_handler_app.utils import log_helper


class WebAppHelper( object ):
        """ Contains support functions for usep_gh_handler.py """

    def __init__( self, log ):
        """ Settings. """
        # self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        # self.TEMP_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__TEMP_DATA_DIR_PATH') )
        # self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
        self.log = log

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
