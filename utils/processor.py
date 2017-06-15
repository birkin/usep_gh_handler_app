# -*- coding: utf-8 -*-

"""
Contains:
- Puller() class, for running git-pull.
- Copier() class, for moving files from the local git directory to the web-accessible unified-inscription directory.
- XIncludeUpdater() class, for updating inscription xi:include references.
- Three job-queue caller functions (one for each class).
"""

import datetime, json, logging, logging.config, os, pprint, shutil, time
import envoy, redis, rq
from usep_gh_handler_app.utils import log_helper


LOG_CONF_JSN = unicode( os.environ[u'usep_gh__WRKR_LOG_CONF_JSN'] )


logging_config_dct = json.loads( LOG_CONF_JSN )
log = logging.getLogger( 'usep_gh_worker_logger' )
logging.config.dictConfig( logging_config_dct )
log.debug( 'logging ready' )


class Puller( object ):
    """ Contains funcions for executing git-pull. """

    # def __init__( self, log ):
    #     """ Settings. """
    #     self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
    #     self.log = log

    def __init__( self ):
        """ Settings. """
        self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
        self.log = log

    def call_git_pull( self ):
        """ Runs git_pull.
                Returns list of filenames.
            Called by run_call_git_pull(). """
        log.debug( 'starting git_pull()' )
        original_directory = os.getcwd()
        os.chdir( self.GIT_CLONED_DIR_PATH )
        command = u'git pull'
        log.debug( 'about to hit envoy' )
        try:
            r = envoy.run( command.encode(u'utf-8') )  # envoy requires strings
            log.debug( 'got envoy output' )
        except Exception as e:
            log.error( 'envoy error, ```{}```'.format( unicode(repr(e)) ) )
        # log_helper.log_envoy_output( self.log, r )
        try:
            log_helper.log_envoy_output( r )
            log.debug( 'envoy output logged' )
        except Exception as e:
            log.error( 'error logging envoy output, ```{}```'.format( unicode(repr(e)) ) )
        os.chdir( original_directory )
        log.debug( 'leaving git_pull()' )
        return

    ## end class Puller()


class Copier( object ):
    """ Contains functions for copying xml-data files. """

    # def __init__( self, log ):
    #     """ Settings. """
    #     self.GIT_CLONED_DIR_PATH = unicode( os.environ.get(u'usep_gh__GIT_CLONED_DIR_PATH') )
    #     self.TEMP_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__TEMP_DATA_DIR_PATH') )
    #     self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
    #     self.log = log

    def __init__( self ):
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


class XIncludeUpdater( object ):
    """ Contains functions for updating inscription <xi:include references.
        The xi:include references have to be change because
            the folder structure as exists for editors and on github is slightly different than in web-app.
        Occurs after copy to unified inscription directory. """

    def __init__( self, log ):
        """ Settings. """
        self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
        self.log = log

    def update_xinclude_references( self ):
        """ Updates xi:include href entries.
            Called by run_xinclude_updater() """
        self.log.debug( u'in utils.processor.XIncludeUpdater.update_xinclude_references(); starting.' )
        inscriptions_filepath_list = self._make_inscriptions_filepath_list()
        for path in inscriptions_filepath_list:
            xml = self._open_file( path )
            updated_xml = self._update_xml( xml )
            with open( path, u'w' ) as f:
                f.write( updated_xml.encode(u'utf-8') )
        return

    def _make_inscriptions_filepath_list( self ):
        """ Builds and returns a list of inscription filepaths.
            Called by update_xinclude_references() """
        inscriptions_web_dir_path = u'%s/inscriptions/' % self.WEBSERVED_DATA_DIR_PATH
        contents = []
        contents_try = os.listdir( inscriptions_web_dir_path )
        for entry in contents_try:
            if entry[-4:] == u'.xml':
                contents.append( u'%s/%s' % (inscriptions_web_dir_path, entry) )
        return contents

    def _open_file( self, path ):
        """ Returns unicode xml string.
            Called by update_xinclude_references() """
        with open( path ) as f:
            xml = f.read()
        if type( xml ) == str:
            xml = xml.decode( u'utf-8' )
        assert type( xml ) == unicode, type( xml )
        return xml

    def _update_xml( self, xml ):
        """ Returns updated unicode xml string.
            Called by update_xinclude_references() """
        mapper = {
            u'http://library.brown.edu/usep_data/resources/include_publicationStmt.xml': u'../resources/include_publicationStmt.xml',
            u'http://library.brown.edu/usep_data/resources/include_taxonomies.xml': u'../resources/include_taxonomies.xml',
            u'http://library.brown.edu/usep_data/resources/titles.xml': u'../resources/titles.xml'
        }
        for (key, value) in mapper.items():
            xml = xml.replace( key, value )
            if type( xml ) == str:
                xml = xml.decode( u'utf-8' )
            assert type( xml ) == unicode, type( xml )
        return xml

    # end class XIncludeUpdater()


## runners ##

q = rq.Queue( u'usep', connection=redis.Redis() )

# def run_call_git_pull( files_to_process ):
#     """ Initiates a git pull update.
#             Spawns a call to Processor.process_file() for each result found.
#         Triggered by usep_gh_handler.handle_github_push(). """
#     log = log_helper.setup_logger()
#     assert sorted( files_to_process.keys() ) == [ u'files_removed', u'files_updated', u'timestamp']; log.debug( u'in utils.processor.run_call_git_pull(); files_to_process, `%s`' % pprint.pformat(files_to_process) )
#     time.sleep( 2 )  # let any existing jobs in process finish
#     ( puller, copier ) = ( Puller(log), Copier(log) )
#     puller.call_git_pull()
#     ( files_to_update, files_to_remove ) = ( copier.get_files_to_update(files_to_process), copier.get_files_to_remove(files_to_process) )
#     log.debug( u'in utils.processor.run_call_git_pull(); enqueuing next job' )
#     q.enqueue_call(
#         func=u'usep_gh_handler_app.utils.processor.run_copy_files',
#         kwargs={u'files_to_update': files_to_update, u'files_to_remove': files_to_remove} )
#     return

def run_call_git_pull( files_to_process ):
    """ Initiates a git pull update.
            Spawns a call to Processor.process_file() for each result found.
        Triggered by usep_gh_handler.handle_github_push(). """
    # log = log_helper.setup_logger()
    log.debug( u'starting pull call' )
    assert sorted( files_to_process.keys() ) == [ u'files_removed', u'files_updated', u'timestamp']; log.debug( u'files_to_process, ```%s```' % pprint.pformat(files_to_process) )
    time.sleep( 2 )  # let any existing jobs in process finish
    # ( puller, copier ) = ( Puller(log), Copier(log) )
    ( puller, copier ) = ( Puller(), Copier() )
    puller.call_git_pull()
    ( files_to_update, files_to_remove ) = ( copier.get_files_to_update(files_to_process), copier.get_files_to_remove(files_to_process) )
    # log.debug( u'in utils.processor.run_call_git_pull(); enqueuing next job' )
    log.debug( u'enqueuing next job' )
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
        func=u'usep_gh_handler_app.utils.processor.run_xinclude_updater',
        kwargs={u'files_to_update': files_to_update, u'files_to_remove': files_to_remove} )
    return

def run_xinclude_updater( files_to_update, files_to_remove ):
    """ Updates the three <xi:include href="../path/inscription.xml"> hrefs in each inscription file.
        Reason is that the folder structure as exists for editors and on github is slightly different than in web-app.
        Triggered bu utils.processor.run_copy_files(). """
    log = log_helper.setup_logger()
    log.debug( u'in utils.processor.run_call_xinclude_replacer(); starting' )
    assert type( files_to_update ) == list; assert type( files_to_remove ) == list
    xinclude_updater = XIncludeUpdater( log )
    xinclude_updater.update_xinclude_references()
    log.debug( u'in processor.run_call_xinclude_updater(); enqueuing next job' )
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.indexer.run_update_index',
        kwargs={u'files_updated': files_to_update, u'files_removed': files_to_remove} )
    return
