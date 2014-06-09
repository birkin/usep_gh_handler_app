# -*- coding: utf-8 -*-

import os, pprint
import redis, rq, solr
from usep_gh_handler_app.utils import log_helper
from usep_gh_handler_app.utils.indexer_parser import Parser


class Indexer( object ):
    """ Contains functions for hitting solr. """

    def __init__( self, log ):
        """ Settings. """
        self.log = log
        self.solr_dict = {}
        self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )
        self.SOLR_URL = unicode( os.environ.get(u'usep_gh__SOLR_URL') )

    ## update index entry ##

    def update_index_entry( self, updated_file_path ):
        """ Updates solr index for a new or changed file.
            Called by run_update_index().
            TODO: replace pq extracts with straight lxml or beautifulsoup extracts. """
        self.log.debug( u'in utils.indexer.update_index_entry(); updated_file_path, `%s`' % updated_file_path )
        full_file_path = u'%s/%s' % ( self.WEBSERVED_DATA_DIR_PATH, updated_file_path )
        self._build_solr_dict( full_file_path )
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

    def remove_index_entry( self ):
        """ Updates solr index for a removed file. """
        pass

    ## enqueue checking functions

    def check_updated_file_path( updated_file_path, worthwhile_dirs ):
        """ Checks whether file updated requires an index job.
            Called by run_update_index(). """
        response = False
        for updated_file_path in files_updated:
            for dir in worthwhile_dirs:
                if dir in updated_file_path:
                    response = True
                    break
        return response

    def check_removed_file_path( removed_file_path, worthwhile_dirs ):
        """ Checks whether file removed requires an index job.
            Called by run_update_index(). """
        response = False
        for removed_file_path in files_removed:
            for dir in worthwhile_dirs:
                if dir in removed_file_path:
                    response = True
                    break
        return response

    ## end class Indexer()


## queue runners ##

def run_update_index( files_updated, files_removed ):
    """ Creates index jobs (doesn't actually call Indexer() directly.
        Triggered by utils.processor.run_copy_files(). """
    log = log_helper.setup_logger()
    indexer = Indexer( log )
    worthwhile_dirs = [ u'bib_only', u'metadata_only', u'transcribed' ]
    for updated_file_path in files_updated:
        if indexer.check_updated_file_path( updated_file_path, worthwhile_dirs ):
            q.enqueue_call(
                func=u'usep_gh_handler_app.utils.indexer.run_update_entry', kwargs={u'updated_file_path': updated_file_path} )
    for removed_file_path in files_updated:
        if indexer.check_removed_file_path( removed_file_path, worthwhile_dirs ):
            q.enqueue_call(
                func=u'usep_gh_handler_app.utils.indexer.run_update_entry', kwargs={u'updated_file_path': updated_file_path} )
    return

def run_update_entry( updated_file_path ):
    """ Updates solr index for a new or changed file.
        Triggered by run_update_index(). """
    log = log_helper.setup_logger()
    indexer = Indexer( log )
    indexer.update_index_entry( updated_file_path )
    return


def run_remove_entry( removed_file_path ):
    """ Updates solr index for removed file.
        Triggered by run_update_index(). """
    log = log_helper.setup_logger()
    indexer = Indexer( log )
    indexer.remove_index_entry( removed_file_path )
    return
