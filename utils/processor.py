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




class XIncludeUpdater( object ):
    """ Contains functions for updating inscription <xi:include references.
        Reason is that the folder structure as exists for editors and on github is slightly different than in web-app."""

    def __init__( self, log ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.log = log

    def update_xinclude_references( self, files_to_update ):
        """ Updates xi:include href entries.
            `files_to_update` is a list like: [ u'xml_inscriptions/metadata_only/CA.Berk.UC.HMA.L.8-4286.xml', u'etc' ] """
        self.log.debug( u'in utils.processor.XIncludeUpdater.update_xinclude_references(); starting.' )
        for inscription_path_segment in files_to_update:
            full_file_path = u'%s/%s' % ( self.GIT_CLONED_DIR_PATH, inscription_path_segment )
            self.log.debug( u'in utils.processor.XIncludeUpdater.update_xinclude_references(); updating file, `%s`' % full_file_path )
            initial_xml = self._load_xml( full_file_path )
            self.log.debug( u'in utils.processor.XIncludeUpdater.update_xinclude_references(); initial_xml, `%s`' % initial_xml[0:500] )
            updated_xml = self._update_xml( initial_xml )
            self.log.debug( u'in utils.processor.XIncludeUpdater.update_xinclude_references(); updated_xml, `%s`' % updated_xml[0:500] )
            with open( full_file_path, u'w' ) as f:
                f.write( updated_xml )
        return

    def _load_xml( self, full_file_path ):
        """ Loads and returns xml unicode string.
            Called by update_xinclude_references(). """
        with open( full_file_path ) as f:
            xml = f.read()
        if type( xml ) == u'str':
            xml = xml.decode( u'utf-8' )
        return xml

    def _update_xml( self, initial_xml ):
        """ Updates and returns xml. """
        modified_xml = initial_xml
        mapper = {
            u'http://library.brown.edu/usep_data/resources/include_publicationStmt.xml': u'../resources/include_publicationStmt.xml',
            u'http://library.brown.edu/usep_data/resources/include_taxonomies.xml': u'../resources/include_taxonomies.xml',
            u'http://library.brown.edu/usep_data/resources/titles.xml': u'../resources/titles.xml',
        }
        for (key, value) in mapper.items():
            modified_xml = modified_xml.replace( key, value )
        return modified_xml

    # def _update_xml( self, initial_xml ):
    #     """ Updates and returns xml. """
    #     mapper = {
    #         u'http://library.brown.edu/usep_data/resources/include_publicationStmt.xml': u'../resources/include_publicationStmt.xml',
    #         u'http://library.brown.edu/usep_data/resources/include_taxonomies.xml': u'../resources/include_taxonomies.xml',
    #         u'http://library.brown.edu/usep_data/resources/titles.xml': u'../resources/titles.xml',
    #     }
    #     for (key, value) in mapper.items():
    #         modified_xml = initial_xml.replace( key, value )
    #     return modified_xml

    # def update_xinclude_references( files_to_update ):
    #     """ Updates xi:include href entries.
    #         `files_to_update` is a list like: [ u'xml_inscriptions/metadata_only/CA.Berk.UC.HMA.L.8-4286.xml', u'etc' ] """
    #     self.log.debug( u'in utils.processor.XIncludeUpdater.update_xinclude_references(); starting.'
    #     for inscription_path_segment in files_to_update:
    #         full_file_path = u'%s/%s' % ( self.GIT_CLONED_DIR_PATH, inscription_path_segment )
    #         self.log.debug( u'in utils.processor.XIncludeUpdater.update_xinclude_references(); updating file, `%s`' % full_file_path )
    #         with open( full_file_path ) as f:
    #             xml = f.read()
    #         if type( xml ) == u'str':
    #             xml = xml.decode( u'utf-8' )
    #         mapper = {
    #             u'http://library.brown.edu/usep_data/resources/include_publicationStmt.xml': u'../resources/include_publicationStmt.xml',
    #             u'http://library.brown.edu/usep_data/resources/include_taxonomies.xml': u'../resources/include_taxonomies.xml',
    #             u'http://library.brown.edu/usep_data/resources/titles.xml': u'../resources/titles.xml',
    #         }
    #         for (key, value) in mapper.items():
    #             xml = xml.replace( key, value )
    #         with open( full_file_path, u'w' ) as f:
    #             f.write( xml )
    #     return

    # end class XIncludeUpdater()





class Copier( object ):
    """ Contains functions for copying xml-data files. """

    def __init__( self, log ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.TEMP_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__TEMP_DATA_DIR_PATH') )
        self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
        self.log = log

    def get_files_to_update( self, files_to_process ):
        """ Creates and returns list of filepaths to copy.
            Used for updating solr.
            Called by run_call_git_pull(). """
        if files_to_process[u'files_updated'] == [ u'all' ]:
            filepaths_to_update = self.make_complete_files_to_update_list()  # TODO
        else:
            filepaths_to_update = files_to_process[u'files_updated']
        self.log.debug( u'in utils.processor.Copier.get_files_to_update(); filepaths_to_update, `%s`' % filepaths_to_update )
        return filepaths_to_update

    def get_files_to_remove( self, files_to_process ):
        """ Creates and returns list of filepaths to remove.
            Used for updating solr.
            Called by run_call_git_pull(). """
        if files_to_process[u'files_removed'] == [ u'check' ]:
            filepaths_to_remove = self.make_complete_files_to_remove_list()  # TODO
        else:
            filepaths_to_remove = files_to_process[u'files_removed']
        self.log.debug( u'in utils.processor.Copier.get_files_to_remove(); filepaths_to_remove, `%s`' % filepaths_to_remove )
        return filepaths_to_remove

    ## copy files

    def copy_files( self ):
        """ Runs rsync.
            Called by run_call_git_pull(). """
        self._copy_resources()
        self._build_unified_inscriptions()
        self._copy_inscriptions()
        return

    def _copy_resources( self ):
        """ Updates resources directory. """
        resources_source_path = u'%s/resources/' % self.GIT_CLONED_DIR_PATH
        resources_destination_path = u'%s/resources/' % self.WEBSERVED_DATA_DIR_PATH
        command = u'rsync -avz --delete %s %s' % ( resources_source_path, resources_destination_path )
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        log_helper.log_envoy_output( self.log, r )
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
            log_helper.log_envoy_output( self.log, r )
            time.sleep( 1 )
        return

    def _copy_inscriptions( self ):
        """ Updates inscriptions directory. """
        inscriptions_source_path = u'%s/' % self.TEMP_DATA_DIR_PATH  # trailing slash important on source directory for rsync
        inscriptions_destination_path = u'%s/inscriptions' % self.WEBSERVED_DATA_DIR_PATH
        command = u'rsync -avz --delete %s %s' % ( inscriptions_source_path, inscriptions_destination_path )
        r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
        log_helper.log_envoy_output( self.log, r )
        return

    ## end class Copier()


## runners ##

q = rq.Queue( u'usep', connection=redis.Redis() )

# def run_call_git_pull( files_to_process ):
#     """ Initiates a git pull update.
#             Spawns a call to Processor.process_file() for each result found.
#         Triggered by usep_gh_handler.handle_github_push(). """
#     log = log_helper.setup_logger()
#     assert sorted( files_to_process.keys() ) == [ u'files_removed', u'files_updated', u'timestamp']
#     log.debug( u'in processor.run_call_git_pull(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
#     time.sleep( 2 )  # let any existing jobs in process finish
#     ( puller, copier ) = ( Puller(log), Copier(log) )
#     puller.call_git_pull()
#     ( files_to_update, files_to_remove ) = ( copier.get_files_to_update(files_to_process), copier.get_files_to_remove(files_to_process) )
#     log.debug( u'in processor.run_call_git_pull(); enqueuing next job' )
#     q.enqueue_call(
#         func=u'usep_gh_handler_app.utils.processor.run_copy_files',
#         kwargs={u'files_to_update': files_to_update, u'files_to_remove': files_to_remove} )
#     return

def run_call_git_pull( files_to_process ):
    """ Initiates a git pull update.
            Spawns a call to Processor.process_file() for each result found.
        Triggered by usep_gh_handler.handle_github_push(). """
    log = log_helper.setup_logger()
    assert sorted( files_to_process.keys() ) == [ u'files_removed', u'files_updated', u'timestamp']
    log.debug( u'in processor.run_call_git_pull(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
    time.sleep( 2 )  # let any existing jobs in process finish
    ( puller, copier ) = ( Puller(log), Copier(log) )
    puller.call_git_pull()
    ( files_to_update, files_to_remove ) = ( copier.get_files_to_update(files_to_process), copier.get_files_to_remove(files_to_process) )
    log.debug( u'in processor.run_call_git_pull(); enqueuing next job' )
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.processor.run_call_xinclude_updater',
        kwargs={u'files_to_update': files_to_update, u'files_to_remove': files_to_remove} )
    return



def run_call_xinclude_updater( files_to_update, files_to_remove ):
    """ Updates the three <xi:include href="../path/inscription.xml"> hrefs in each inscription file.
        Reason is that the folder structure as exists for editors and on github is slightly different than in web-app.
        Triggered bu utils.processor.run_call_git_pull(). """
    log = log_helper.setup_logger()
    log.debug( u'in utils.processor.run_call_xinclude_replacer(); starting' )
    assert type( files_to_update ) == list; assert type( files_to_remove ) == list
    xinclude_updater = XIncludeUpdater( log )
    xinclude_updater.update_xinclude_references( files_to_update )
    log.debug( u'in processor.run_call_xinclude_updater(); enqueuing next job' )
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.processor.run_copy_files',
        kwargs={u'files_to_update': files_to_update, u'files_to_remove': files_to_remove} )
    return



def run_copy_files( files_to_update, files_to_remove ):
    """ Runs a copy and then triggers an index job.
        Incoming data not for copying, but to pass to indexer.
        Triggered by utils.processor.run_call_git_pull(). """
    log = log_helper.setup_logger()
    log.debug( u'in utils.processor.run_copy_files(); starting' )
    assert type( files_to_update ) == list; assert type( files_to_remove ) == list
    log.debug( u'in utils.processor.run_copy_files(); files_to_update, `%s`' % pprint.pformat(files_to_update) )
    log.debug( u'in utils.processor.run_copy_files(); files_to_remove, `%s`' % pprint.pformat(files_to_remove) )
    copier = Copier( log )
    copier.copy_files()
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.indexer.run_update_index',
        kwargs={u'files_updated': files_to_update, u'files_removed': files_to_remove} )
    return
