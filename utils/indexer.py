# -*- coding: utf-8 -*-

import glob, os, pprint
import redis, rq, solr
from usep_gh_handler_app.utils import log_helper
from usep_gh_handler_app.utils.indexer_parser import Parser


class Indexer( object ):
    """ Contains functions for hitting solr.
        TODO: Refactor so the index-removal can take ids instead of filenames.
              That way, it can be called from the reindex-all code, too. """

    def __init__( self, log ):
        """ Settings. """
        self.log = log
        self.solr_dict = {}
        self.worthwhile_dirs = [ u'bib_only', u'metadata_only', u'transcribed' ]  # only need to update index for these dirs
        self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
        self.SOLR_URL = unicode( os.environ.get(u'usep_gh__SOLR_URL') )
        self.BIB_XML_PATH = unicode( os.environ.get(u'usep_gh__BIB_XML_PATH') )

    ## update index entry ##

    def update_index_entry( self, filename ):
        """ Updates solr index for a new or changed file.
            Called by run_update_index().
            TODO: replace pq extracts with straight lxml or beautifulsoup extracts. """
        self.log.debug( u'in utils.indexer.update_index_entry(); filename, `%s`' % filename )
        full_file_path = u'%s/inscriptions/%s' % ( self.WEBSERVED_DATA_DIR_PATH, filename )
        self._build_solr_dict( full_file_path, self.BIB_XML_PATH )
        self._post_solr_update()
        return

    def _build_solr_dict( self, inscription_xml_path, bib_xml_path ):
        """ Calls parser to build the solr dict.
            Called by update_index_entry(). """
        p = Parser( inscription_xml_path, bib_xml_path, self.log )
        self.solr_dict[u'id'] = p.i_id; assert not p.i_id == None
        self.solr_dict[u'bib_ids'] = p.bib_ids
        self.solr_dict[u'bib_ids_filtered'] = p.parseBibIdsFiltered()
        self.solr_dict[u'bib_ids_types'] = p.parseBibIdsTypes()
        self.solr_dict[u'title'] = p.parseTitle()
        self.solr_dict[u'text_genre'] = p.parse_text_genre()
        self.solr_dict[u'object_type'] = p.parse_object_type()
        self.solr_dict[u'bib_titles'] = p.parseBibTitles()
        self.solr_dict[u'bib_titles_all'] = p.bib_titles_all
        self.solr_dict[u'bib_authors'] = p.parseBibAuthors()
        self.solr_dict[u'condition'] = p.parseCondition()
        self.solr_dict[u'decoration'] = p.parseDecoration()
        self.solr_dict[u'fake'] = p.parseFake()
        self.solr_dict[u'graphic_name'] = p.parse_graphic_name()
        self.solr_dict[u'language'] = p.parseLanguage()
        self.solr_dict[u'material'] = p.parseMaterial()
        self.solr_dict[u'msid_region'] = p.parseMsidRegion()
        self.solr_dict[u'msid_settlement'] = p.parseMsidSettlement()
        self.solr_dict[u'msid_institution'] = p.parseMsidInstitution()
        self.solr_dict[u'msid_repository'] = p.parseMsidRepository()
        self.solr_dict[u'msid_idno'] = p.parseMsidIdno()
        self.solr_dict[u'status'] = p.parseStatus()
        self.solr_dict[u'writing'] = p.parseWriting()
        self.log.debug( u'in utils.indexer.Indexer._build_solr_dict(); solr_dict, `%s`' % pprint.pformat(self.solr_dict) )
        return self.solr_dict

    def _post_solr_update( self ):
        """ Updates existing solr entry.
            Called by update_index_entry(). """
        self.log.debug( u'in utils.indexer.Indexer._post_solr_update(); self.SOLR_URL is: `%s`' % self.SOLR_URL )
        s = solr.Solr( self.SOLR_URL )
        response = s.add( self.solr_dict )
        s.commit()
        s.close()
        self.log.debug( u'in utils.indexer.Indexer._post_solr_update(); post complete; response is: %s' % response )
        return

    ## remove index entry ##

    def remove_index_entry( self, filename=None, inscription_id=None ):
        """ Updates solr index for a removed file. """
        if filename:
            inscription_id = filename.strip().split(u'.xml')[0]
        self.log.debug( u'in utils.indexer.Indexer.remove_index_entry(); filename, `%s`; inscription_id, `%s`: `%s`' % (filename, inscription_id) )
        s = solr.Solr( self.SOLR_URL )
        response = s.delete( id=inscription_id )
        s.commit()
        s.close()
        self.log.debug( u'in utils.indexer.Indexer.remove_index_entry(); post complete; response is: %s' % response )
        return

    # def remove_index_entry( self, filename ):
    #     """ Updates solr index for a removed file. """
    #     inscription_id = filename.strip().split(u'.xml')[0]
    #     self.log.debug( u'in utils.indexer.Indexer.remove_index_entry(); filename, `%s`; inscription_id, `%s`: `%s`' % (filename, inscription_id) )
    #     s = solr.Solr( self.SOLR_URL )
    #     response = s.delete( id=inscription_id )
    #     s.commit()
    #     s.close()
    #     self.log.debug( u'in utils.indexer.Indexer.remove_index_entry(); post complete; response is: %s' % response )
    #     return

    ## enqueue checking functions

    def check_updated_file_path( self, updated_file_path ):
        """ Checks whether file updated requires an index job.
            Called by run_update_index(). """
        response = False
        for dir in self.worthwhile_dirs:
            if dir in updated_file_path:
                response = True
                break
        return response

    def check_removed_file_path( self, removed_file_path ):
        """ Checks whether file removed requires an index job.
            Called by run_update_index(). """
        response = False
        for dir in self.worthwhile_dirs:
            if dir in removed_file_path:
                response = True
                break
        return response

    ## end class Indexer()


## runners ##

q = rq.Queue( u'usep', connection=redis.Redis() )

def run_update_index( files_updated, files_removed ):
    """ Creates index jobs (doesn't actually call Indexer() directly.
        Triggered by utils.processor.run_copy_files(). """
    log = log_helper.setup_logger()
    indexer = Indexer( log )
    for updated_file_path in files_updated:
        if indexer.check_updated_file_path( updated_file_path ):
            q.enqueue_call(
                func=u'usep_gh_handler_app.utils.indexer.run_update_entry', kwargs={u'updated_file_path': updated_file_path} )
    for removed_file_path in files_removed:
        if indexer.check_removed_file_path( removed_file_path ):
            q.enqueue_call(
                func=u'usep_gh_handler_app.utils.indexer.run_remove_entry', kwargs={u'removed_file_path': removed_file_path} )
    return

def run_update_entry( updated_file_path ):
    """ Updates solr index for a new or changed file.
        Triggered by run_update_index(), and utils.reindex_all_support.run_enqueue_all_index_updates(). """
    log = log_helper.setup_logger()
    indexer = Indexer( log )
    filename = updated_file_path.split( u'/' )[-1]
    indexer.update_index_entry( filename )
    return

def run_remove_entry( removed_file_path ):
    """ Updates solr index for removed file.
        Triggered by run_update_index(). """
    log = log_helper.setup_logger()
    indexer = Indexer( log )
    filename = removed_file_path.split( u'/' )[-1]
    indexer.remove_index_entry( filename=filename )
    return

def run_remove_entry_via_id( inscription_id ):
    """ Removes id from solr.
        Triggered by utils.reindex_all_support.run_enqueue_all_index_updates(). """
    log = log_helper.setup_logger()
    indexer = Indexer( log )
    indexer.remove_index_entry( inscription_id=inscription_id )
    return
