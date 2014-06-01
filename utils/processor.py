# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, shutil, time
import envoy, redis, rq
from usep_gh_handler_app.utils import log_helper


class Puller( object ):
    """ Contains funcions for executing git-pull. """

    def __init__( self, log ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.log = log

    def call_git_pull( self ):
        """ Runs git_pull.
                Returns list of filenames.
            Called by run_call_git_pull(). """
        original_directory = os.getcwd()
        os.chdir( self.GIT_CLONED_DIR_PATH )
        command = u'git pull'
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        log_helper.log_envoy_output( self.log, r )
        os.chdir( original_directory )
        return


class Copier( object ):
    """ Contains functions for copying xml-data files. """

    def __init__( self, log ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.TEMP_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__TEMP_DATA_DIR_PATH') )
        self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
        self.log = log

    def get_files_to_copy( self, files_to_process ):
        """ Creates and returns list of filepaths to copy.
            Used for updating solr.
            Called by run_call_git_pull(). """
        if files_to_process[u'to_copy'] == [ u'all' ]:
            filepaths_to_copy = self.make_complete_files_to_copy_list()  # TODO
        else:
            filepaths_to_copy = files_to_process[u'to_copy']
        self.log.debug( u'in utils.Processor.get_files_to_copy(); filepaths_to_copy, `%s`' % filepaths_to_copy )
        return filepaths_to_copy

    def get_files_to_remove( self, files_to_process ):
        """ Creates and returns list of filepaths to remove.
            Used for updating solr.
            Called by run_call_git_pull(). """
        if files_to_process[u'to_remove'] == [ u'check' ]:
            filepaths_to_remove = self.make_complete_files_to_remove_list()  # TODO
        else:
            filepaths_to_remove = files_to_process[u'to_remove']
        self.log.debug( u'in utils.Processor.get_files_to_remove(); filepaths_to_remove, `%s`' % filepaths_to_remove )
        return filepaths_to_remove

    ## copy files

    def copy_files( self ):
        """ Runs rsync.
            Called by run_call_git_pull(). """
        self._copy_resources()
        self._build_unified_inscriptions()
        self._copy_inscriptions()

    def _copy_resources( self ):
        """ Updates resources directory. """
        resources_source_path = u'%s/%s' % ( self.GIT_CLONED_DIR_PATH, u'resources' )
        resources_destination_path = u'%s/%s' % ( self.WEBSERVED_DATA_DIR_PATH, u'resources' )
        command = u'rsync -avz --delete %s %s' % ( resources_source_path, resources_destination_path )
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        return

    def _build_unified_inscriptions( self ):
        """ Updates staging unified inscrptions file. """
        for entry in os.listdir( self.TEMP_DATA_DIR_PATH ):  # deletes old temp unified inscriptions
            file_path = os.path.join( self.TEMP_DATA_DIR_PATH, entry )
            os.unlink( file_path )
        source_dir_paths = [  # runs 3 non-deletion rsyncs
            u'%s/xml_inscriptions/bib_only' % self.GIT_CLONED_DIR_PATH,
            u'%s/xml_inscriptions/metadata_only' % self.GIT_CLONED_DIR_PATH,
            u'%s/xml_inscriptions/transcription' % self.GIT_CLONED_DIR_PATH ]
        for source_dir_path in source_dir_paths:
            command = u'rsync -avz %s %s' % ( source_dir_path, resources_destination_path, self.TEMP_DATA_DIR_PATH )
            r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        return

    def _copy_inscriptions( self ):
        """ Updates inscriptions directory. """
        inscriptions_source_path = self.TEMP_DATA_DIR_PATH
        inscriptions_destination_path = u'%s/%s' % ( self.WEBSERVED_DATA_DIR_PATH, u'inscriptions' )
        command = u'rsync -avz --delete %s %s' % ( inscriptions_source_path, inscriptions_destination_path )
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        return

    ## end class ProcessorUtils()


# class Processor( object ):
#     """ Contains functions to process an individual file. """

#     def __init__( self, log ):
#         """ Settings. """
#         self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
#         self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
#         self.log = log

    # def copy_file( self, filepath ):
    #     """ Handles inscription and resource copying appropriately.
    #         Returns inscription_id if appropriate. """
    #     inscription_sub_directories = [ u'bib_only', u'metadata_only', u'transcription' ]
    #     copy_type = u'resource'
    #     for dir_name in inscription_sub_directories:
    #         if dir_name in filepath:
    #             copy_type = u'inscription'
    #             break
    #     return_dict = {}
    #     if copy_type == u'inscription':
    #         file_name = filepath.split(u'/')[-1]
    #         source_path = u'%s/%s' % ( self.GIT_CLONED_DIR_PATH, filepath )  # filepath doesn't include path _to_ usep_data dir
    #         destination_path = u'%s/xml_inscriptions/%s' % ( self.WEBSERVED_DATA_DIR_PATH, file_name )
    #         shutil.copy2( source_path, destination_path )
    #         inscription_id = file_name.split( u'.xml' )[0]
    #         return_dict = { u'inscription_id': inscription_id }
    #     else:
    #         processor_utils = ProcessorUtils( log )
    #         source_path = u'%s/%s' % ( self.GIT_CLONED_DIR_PATH, u'resources' )
    #         destination_path = u'%s/%s' % ( self.self.WEBSERVED_DATA_DIR_PATH, u'resources' )
    #         # rsync -avz --delete /Users/birkin/Desktop/folder_a/ /Users/birkin/Desktop/folder_b/
    #         command = u'rsync -avz --delete %s %s' % ( source_path, destination_path )
    #         r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
    #         processor_utils.log_envoy_output( r )
    #     return return_dict


## queue runners ##

q = rq.Queue( u'usep', connection=redis.Redis() )

def run_call_git_pull( files_to_process ):
    """ Initiates a git pull update.
            Spawns a call to Processor.process_file() for each result found.
        Triggered by usep_gh_handler.handle_github_push(). """
    log = log_helper.setup_logger()
    assert sorted( files_to_process.keys() ) == [ u'timestamp', u'to_copy', u'to_remove' ]; log.debug( u'in processor.run_call_git_pull(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
    time.sleep( 2 )  # let any existing jobs in process finish
    ( puller, copier ) = ( Puller(log), Copier(log) )
    puller.call_git_pull()
    ( files_to_copy, files_to_remove ) = ( copier.get_files_to_copy(files_to_process), copier.get_files_to_remove(files_to_process) )
    if files_to_copy or files_to_remove:
        q.enqueue_call(
            func=u'usep_gh_handler_app.utils.processor.run_copy_files',
            kwargs={u'files_to_copy': files_to_copy, u'files_to_remove': files_to_remove} )
    return

# def run_call_git_pull( files_to_process ):
#     """ Initiates a git pull update.
#             Spawns a call to Processor.process_file() for each result found.
#         Triggered by usep_gh_handler.handle_github_push(). """
#     log = log_helper.setup_logger()
#     assert sorted( files_to_process.keys() ) == [ u'timestamp', u'to_copy', u'to_remove' ]; log.debug( u'in processor.run_call_git_pull(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
#     time.sleep( 2 )  # let any existing jobs in process finish
#     processor_utils = ProcessorUtils( log )
#     processor_utils.call_git_pull()
#     ( files_to_copy, files_to_remove ) = ( processor_utils.get_files_to_copy(files_to_process), processor_utils.get_files_to_remove(files_to_process) )
#     for filepath in files_to_copy:
#         job = q.enqueue_call( func=u'usep_gh_handler_app.utils.processor.run_copy_file', kwargs = {u'filepath': filepath} )
#     for filepath in files_to_remove:
#         job = q.enqueue_call( func=u'usep_gh_handler_app.utils.processor.run_remove_file', kwargs = {u'filepath': filepath} )
#     return

def run_copy_files( files_to_copy, files_to_remove ):
    """ Runs a copy and then triggers an index job if necessary.
        Triggered by utils.processor.run_call_git_pull(). """
    log = log_helper.setup_logger()
    assert type( files_to_copy ) == list; assert type( files_to_remove ) == list
    log.debug( u'in utils.processor.run_copy_files(); files_to_copy, `%s`' % pprint.pformat(files_to_copy) )
    log.debug( u'in utils.processor.run_copy_files(); files_to_remove, `%s`' % pprint.pformat(files_to_remove) )
    copier = Copier( log )
    copier.copy_files()
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.processor.run_update_index',
        kwargs={u'files_to_copy': files_to_copy, u'files_to_remove': files_to_remove} )
    return

# def run_copy_file( filepath ):
#     """ Runs a copy and then triggers an index job if necessary.
#         Triggered by utils.processor.run_call_git_pull(). """
#     log = log_helper.setup_logger()
#     assert type( filepath ) == unicode
#     log.debug( u'in processor.run_copy_file(); filepath, `%s`' % filepath )
#     processor = Processor( log )
#     copy_result = processor.copy_file( filepath )
#     if copy_result[u'next'] == u'index':
#         job = q.enqueue_call( func=u'usep_gh_handler_app.utils.processor.run_update_index', kwargs = {u'inscription_id': copy_result[u'inscription_id']} )
#     return
