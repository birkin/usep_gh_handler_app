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

    ## end class Puller()


class Copier( object ):
    """ Contains functions for copying xml-data files. """

    def __init__( self, log ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.TEMP_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__TEMP_DATA_DIR_PATH') )
        self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
        # self.resources_destination_path = None  # set by _copy_resources(); accessed by _build_unified_inscriptions()
        self.log = log

    def get_files_to_update( self, files_to_process ):
        """ Creates and returns list of filepaths to copy.
            Used for updating solr.
            Called by run_call_git_pull(). """
        if files_to_process[u'files_updated'] == [ u'all' ]:
            filepaths_to_update = self.make_complete_files_to_update_list()  # TODO
        else:
            filepaths_to_update = files_to_process[u'files_updated']
        self.log.debug( u'in utils.Processor.get_files_to_update(); filepaths_to_update, `%s`' % filepaths_to_update )
        return filepaths_to_update

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
        """ Updates staging unified inscriptions file. """
        bib_command = u'rsync -avz --delete %s %s' % (  # note: uses delete flag to clear out previous data
            u'%s/xml_inscriptions/bib_only/' % self.GIT_CLONED_DIR_PATH, self.TEMP_DATA_DIR_PATH )
        metadata_command = u'rsync -avz %s %s' % (
            u'%s/xml_inscriptions/metadata_only/' % self.GIT_CLONED_DIR_PATH, self.TEMP_DATA_DIR_PATH )
        transcription_command = u'rsync -avz %s %s' % (
            u'%s/xml_inscriptions/transcribed/' % self.GIT_CLONED_DIR_PATH, self.TEMP_DATA_DIR_PATH )
        for command in [ bib_command, metadata_command, transcription_command ]:
            r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
            time.sleep( 1 )
        return

    def _copy_inscriptions( self ):
        """ Updates inscriptions directory. """
        inscriptions_source_path = self.TEMP_DATA_DIR_PATH
        inscriptions_destination_path = u'%s/%s' % ( self.WEBSERVED_DATA_DIR_PATH, u'inscriptions' )
        command = u'rsync -avz --delete %s %s' % ( inscriptions_source_path, inscriptions_destination_path )
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        return

    ## end class Copier()


## queue runners ##

q = rq.Queue( u'usep', connection=redis.Redis() )

def run_call_git_pull( files_to_process ):
    """ Initiates a git pull update.
            Spawns a call to Processor.process_file() for each result found.
        Triggered by usep_gh_handler.handle_github_push(). """
    log = log_helper.setup_logger()
    assert sorted( files_to_process.keys() ) == [ u'files_updated', u'files_removed', u'timestamp']
    log.debug( u'in processor.run_call_git_pull(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
    time.sleep( 2 )  # let any existing jobs in process finish
    ( puller, copier ) = ( Puller(log), Copier(log) )
    puller.call_git_pull()
    ( files_to_update, files_to_remove ) = ( copier.get_files_to_update(files_to_process), copier.get_files_to_remove(files_to_process) )
    log.debug( u'in processor.run_call_git_pull(); enqueuing next job' )
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.processor.run_copy_files',
        kwargs={u'files_to_update': files_to_update, u'files_to_remove': files_to_remove} )
    return

def run_copy_files( files_to_update, files_to_remove ):
    """ Runs a copy and then triggers an index job.
        Incoming data not for copying, but to pass to indexer.
        Triggered by utils.processor.run_call_git_pull(). """
    log = log_helper.setup_logger()
    log.debug( u'in utils.processor.run_copy_files(); startign' )
    assert type( files_to_update ) == list; assert type( files_to_remove ) == list
    log.debug( u'in utils.processor.run_copy_files(); files_to_update, `%s`' % pprint.pformat(files_to_update) )
    log.debug( u'in utils.processor.run_copy_files(); files_to_remove, `%s`' % pprint.pformat(files_to_remove) )
    copier = Copier( log )
    copier.copy_files()
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.indexer.run_update_index',
        kwargs={u'files_updated': files_to_update, u'files_removed': files_to_remove} )
    return
