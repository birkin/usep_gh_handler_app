# -*- coding: utf-8 -*-

import glob, logging, os, pprint
import redis, requests, rq
from usep_gh_handler_app.utils import log_helper
from usep_gh_handler_app.utils.processor import Copier, Puller


LOG_CONF_JSN = unicode( os.environ[u'usep_gh__WRKR_LOG_CONF_JSN'] )


log = logging.getLogger( 'usep_gh_worker_logger' )
if not logging._handlers:  # true when module accessed by queue-jobs
    logging_config_dct = json.loads( LOG_CONF_JSN )
    logging.config.dictConfig( logging_config_dct )


class InscriptionFilenamesBuilder( object ):
    """ Contains functions for building list of inscriptions to be indexed.
        List also used, later, to determine which index entries to remove. """

    def __init__( self ):
        """ Settings. """
        self.inscriptions_dir_path = u'%s/inscriptions/' % unicode( os.environ[u'usep_gh__WEBSERVED_DATA_DIR_PATH'] )

    def build_inscription_filepaths( self ):
        """ Builds list of inscriptions to be indexed.
            Called by run_start_reindex_all(). """
        log.debug( u'in utils.indexer.InscriptionFilenamesBuilder.build_filenames(); self.inscriptions_dir_path, `%s`' % self.inscriptions_dir_path )
        inscriptions = glob.glob( u'%s/*.xml' % self.inscriptions_dir_path )
        log.debug( u'in utils.indexer.InscriptionFilenamesBuilder.build_filenames(); inscriptions[0:3], `%s`' % pprint.pformat(inscriptions[0:3]) )
        return { u'inscriptions': inscriptions }

    ## end class InscriptionFilenamesBuilder()


class SolrIdChecker( object ):
    """ Contains functions for getting solr_ids, and checking them against file-system inscriptions. """

    def __init__( self ):
        """ Settings. """
        self.SOLR_URL = unicode( os.environ[u'usep_gh__SOLR_URL'] )

    def build_orphaned_ids( self, inscriptions ):
        """ Controller for building list of orphaned solr ids that will be deleted.
            Called by run_build_solr_remove_list(). """
        all_solr_ids = self._grab_solr_ids()
        file_system_ids = self._make_file_system_ids( inscriptions )
        ids_to_remove = self._make_ids_to_remove( all_solr_ids, file_system_ids )
        return ( inscriptions, ids_to_remove )

    def _grab_solr_ids( self ):
        """ Returns list of solr ids.
            Called by build_orphaned_ids(). """
        url = u'%s/select?q=*:*&fl=id&rows=100000&wt=json' % self.SOLR_URL
        r = requests.get( url )
        json_dict = r.json()
        docs = json_dict[u'response'][u'docs']  # list of dicts
        doc_list = []
        for doc in docs:
            doc_list.append( doc[u'id'] )
        return sorted( doc_list )

    def _make_file_system_ids( self, inscriptions ):
        """ Returns list of file-system ids.
            Called by build_orphaned_ids(). """
        file_system_ids = []
        for file_path in inscriptions:
            filename = file_path.split( u'/' )[-1]
            inscription_id = filename.strip().split(u'.xml')[0]
            file_system_ids.append( inscription_id )
        log.debug( u'in utils.reindex_all_support._make_file_system_ids(); len(file_system_ids), `%s`' % len(file_system_ids) )
        log.debug( u'in utils.reindex_all_support._make_file_system_ids(); file_system_ids[0:2], `%s`' % pprint.pformat(file_system_ids[0:2]) )
        return file_system_ids

    def _make_ids_to_remove( self, all_solr_ids, file_system_ids ):
        """ Builds and returns list of ids in solr but not in file-system. These will be removed later.
            Called by build_orphaned_ids(). """
        ids_to_remove_set = set(all_solr_ids) - set(file_system_ids)
        ids_to_remove_list = list( ids_to_remove_set )
        log.debug( u'in utils.reindex_all_support._make_ids_to_remove(); len(ids_to_remove_list), `%s`' % len(ids_to_remove_list) )
        log.debug( u'in utils.reindex_all_support._make_ids_to_remove(); ids_to_remove_list[0:2], `%s`' % pprint.pformat(ids_to_remove_list[0:2]) )
        return ids_to_remove_list

    ## end class SolrIdChecker()


## runners

q = rq.Queue( u'usep', connection=redis.Redis() )

def run_call_simple_git_pull():
    """ Initiates a simple git pull update.
        Triggered by usep_gh_handler.reindex_all() """
    log = log_helper.setup_logger()
    puller = Puller()
    puller.call_git_pull()
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.reindex_all_support.run_simple_copy_files',
        kwargs={} )
    return

def run_simple_copy_files():
    """ Runs a copy and then triggers an full_re-index job.
        Triggered by utils.processor.run_call_simple_git_pull(). """
    log = log_helper.setup_logger()
    log.debug( u'in utils.reindex_all_support.run_simple_copy_files(); starting' )
    copier = Copier()
    copier.copy_files()
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.reindex_all_support.run_start_reindex_all',
        kwargs={} )
    return

def run_start_reindex_all():
    """ Starts process by building a list of inscriptions.
        Process:
        - build list of all inscriptions (from file system) that need to be indexed.
        - build list of all inscription_ids that need to be removed,
          meaning inscription_ids that _are_ in solr and are _not_ in the file system inscriptions list.
        - enqueue all add jobs
        - enqueue all remove jobs
        Triggered by utils.processor.run_simple_copy_files().
        """
    log = log_helper.setup_logger()
    filenames_builder = InscriptionFilenamesBuilder()
    inscriptions = filenames_builder.build_inscription_filepaths()
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.reindex_all_support.run_build_solr_remove_list',
        kwargs={u'inscriptions': inscriptions} )
    return

def run_build_solr_remove_list( inscriptions ):
    """ Builds a list of inscription_ids to remove from solr.
        Triggered by run_start_reindex_all(). """
    assert inscriptions.keys() == [ u'inscriptions' ]
    log = log_helper.setup_logger()
    solr_id_checker = SolrIdChecker()
    ( inscriptions_to_index, ids_to_remove ) = solr_id_checker.build_orphaned_ids( inscriptions[u'inscriptions'] )
    q.enqueue_call(
        func=u'usep_gh_handler_app.utils.reindex_all_support.run_enqueue_all_index_updates',
        kwargs={u'inscriptions_to_index': inscriptions_to_index, u'ids_to_remove': ids_to_remove} )
    return

def run_enqueue_all_index_updates( inscriptions_to_index, ids_to_remove ):
    for file_path in inscriptions_to_index:
        q.enqueue_call(
            func=u'usep_gh_handler_app.utils.indexer.run_update_entry',
            kwargs={u'updated_file_path': file_path} )  # updated_file_path just a label; TODO: make name less awkward
    for id_to_remove in ids_to_remove:
        q.enqueue_call(
            func=u'usep_gh_handler_app.utils.indexer.run_remove_entry_via_id',
            kwargs={u'id_to_remove': id_to_remove} )
    return  # done!
