# -*- coding: utf-8 -*-

import redis, rq
from usep_gh_handler_app.utils import log_helper
from usep_gh_handler_app.utils.indexer_parser import Parser


class Indexer( object ):
    """ Contains functions for hitting solr. """

    def __init__( self, log ):
        """ Settings. """
        self.log = logd
        self.solr_dict = {}
        self.WEBSERVED_DATA_DIR_PATH = unicode( os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH') )

    ## update index entry ##

    def update_index_entry( self, updated_file_path ):
        """ Updates solr index for a new or changed file.
            Called by run_update_index().
            TODO: replace pq extracts with straight lxml or beautifulsoup extracts. """
        self.log.debug( u'in utils.indexer.update_index_entry(); updated_file_path, `%s`' % updated_file_path )
        full_file_path = u'%s/%s' % ( self.WEBSERVED_DATA_DIR_PATH, updated_file_path )
        file_name = updated_file_path.split('/')[-1]
        p = Parser( log )
        xml = open( x_entry ).read()
        d_xml = xml.replace( 'xmlns:', 'xmlnamespace:' )  # de-namespacing for easy element addressing
        pq = pq = PyQuery( d_xml )  # pq is now addressable w/jquery syntax
        self._build_solr_dict( p, pq, log )
        self._post_update()
        return

    def _build_solr_dict( p, pq, log ):
        """ Calls parser to build the solr dict. """
        self.solr_dict[u'id'] = p.i_id; assert not p.i_id == None
        self.solr_dict[u'bib_ids'] = p.bib_ids
        self.solr_dict[u'bib_ids_filtered'] = p.parseBibIdsFiltered()
        self.solr_dict[u'bib_ids_types'] = p.parseBibIdsTypes()
        self.solr_dict[u'title'] = p.parseTitle()
        self.solr_dict[u'text_genre'] = p.parse_text_genre( pq )
        self.solr_dict[u'object_type'] = p.parse_object_type( pq )
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
        log.debug( u'in utils.indexer.Indexer._build_solr_dict(); solr_dict, `%s`' % pprint.pformat(self.solr_dict) )
        return

    def _post_update( self ):
        """ Updates existing solr entry. """
        pass

    ## remove index entry ##

    def remove_index_entry( self ):
        """ Updates solr index for a removed file. """
        pass

    ## end class Indexer()


## queue runners ##

def run_update_index( files_updated, files_removed ):
    """ Creates index jobs (doesn't actually call Indexer() directly.
        Triggered by utils.processor.run_copy_files(). """
    1/0
    log = log_helper.setup_logger()
    for updated_file_path in files_updated:
        q.enqueue_call(
            func=u'usep_gh_handler_app.utils.indexer.run_update_entry',
            kwargs={u'updated_file_path': updated_file_path} )
    for removed_file_path in files_removed:
        q.enqueue_call(
            func=u'usep_gh_handler_app.utils.indexer.run_remove_entry',
            kwargs={u'removed_file_path': removed_file_path} )
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
