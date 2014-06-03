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
        """ Calls parser to build the solr dict. """
        p = Parser( inscription_xml_path, bib_xml_path, self.log )
        key = p.i_id; assert not p.i_id == None
        self.solr_dict[key] = {}
        self.solr_dict[key][u'id'] = key
        self.solr_dict[key][u'bib_ids'] = p.bib_ids
        self.solr_dict[key][u'bib_ids_filtered'] = p.parseBibIdsFiltered()
        self.solr_dict[key][u'bib_ids_types'] = p.parseBibIdsTypes()
        self.solr_dict[key][u'title'] = p.parseTitle()
        self.solr_dict[key][u'text_genre'] = p.parse_text_genre()
        self.solr_dict[key][u'object_type'] = p.parse_object_type()
        self.solr_dict[key][u'bib_titles'] = p.parseBibTitles()
        self.solr_dict[key][u'bib_titles_all'] = p.bib_titles_all
        self.solr_dict[key][u'bib_authors'] = p.parseBibAuthors()
        self.solr_dict[key][u'condition'] = p.parseCondition()
        self.solr_dict[key][u'decoration'] = p.parseDecoration()
        self.solr_dict[key][u'fake'] = p.parseFake()
        self.solr_dict[key][u'graphic_name'] = p.parse_graphic_name()
        self.solr_dict[key][u'language'] = p.parseLanguage()
        self.solr_dict[key][u'material'] = p.parseMaterial()
        self.solr_dict[key][u'msid_region'] = p.parseMsidRegion()
        self.solr_dict[key][u'msid_settlement'] = p.parseMsidSettlement()
        self.solr_dict[key][u'msid_institution'] = p.parseMsidInstitution()
        self.solr_dict[key][u'msid_repository'] = p.parseMsidRepository()
        self.solr_dict[key][u'msid_idno'] = p.parseMsidIdno()
        self.solr_dict[key][u'status'] = p.parseStatus()
        self.solr_dict[key][u'writing'] = p.parseWriting()
        self.log.debug( u'in utils.indexer.Indexer._build_solr_dict(); solr_dict, `%s`' % pprint.pformat(self.solr_dict) )
        return self.solr_dict

    # def _build_solr_dict( self, inscription_xml_path, bib_xml_path ):
    #     """ Calls parser to build the solr dict. """
    #     p = Parser( inscription_xml_path, bib_xml_path, self.log )
    #     self.solr_dict[u'id'] = p.i_id; assert not p.i_id == None
    #     self.solr_dict[u'bib_ids'] = p.bib_ids
    #     self.solr_dict[u'bib_ids_filtered'] = p.parseBibIdsFiltered()
    #     self.solr_dict[u'bib_ids_types'] = p.parseBibIdsTypes()
    #     self.solr_dict[u'title'] = p.parseTitle()
    #     self.solr_dict[u'text_genre'] = p.parse_text_genre()
    #     self.solr_dict[u'object_type'] = p.parse_object_type()
    #     self.solr_dict[u'bib_titles'] = p.parseBibTitles()
    #     self.solr_dict[u'bib_titles_all'] = p.bib_titles_all
    #     self.solr_dict[u'bib_authors'] = p.parseBibAuthors()
    #     self.solr_dict[u'condition'] = p.parseCondition()
    #     self.solr_dict[u'decoration'] = p.parseDecoration()
    #     self.solr_dict[u'fake'] = p.parseFake()
    #     self.solr_dict[u'graphic_name'] = p.parse_graphic_name()
    #     self.solr_dict[u'language'] = p.parseLanguage()
    #     self.solr_dict[u'material'] = p.parseMaterial()
    #     self.solr_dict[u'msid_region'] = p.parseMsidRegion()
    #     self.solr_dict[u'msid_settlement'] = p.parseMsidSettlement()
    #     self.solr_dict[u'msid_institution'] = p.parseMsidInstitution()
    #     self.solr_dict[u'msid_repository'] = p.parseMsidRepository()
    #     self.solr_dict[u'msid_idno'] = p.parseMsidIdno()
    #     self.solr_dict[u'status'] = p.parseStatus()
    #     self.solr_dict[u'writing'] = p.parseWriting()
    #     self.log.debug( u'in utils.indexer.Indexer._build_solr_dict(); solr_dict, `%s`' % pprint.pformat(self.solr_dict) )
    #     return self.solr_dict

    def _post_solr_update( self ):
        """ Updates existing solr entry. """
        self.log.debug( u'in utils.indexer.Indexer._post_solr_update(); self.SOLR_URL is: `%s`' % self.SOLR_URL )
        s = solr.Solr( self.SOLR_URL )
        response = s.add( self.solr_dict )
        s.commit()
        s.close()
        self.log.debug( u'in utils.indexer.Indexer._post_solr_update(); post complete; response is: %s' % response )
        return

    # def post_to_solr(self):
    #   ## check
    #   if self.file_data == None:
    #     logger.error( u'in Updater.post_to_solr(); self.file_data must be populated' )
    #     self.update_errors = True
    #     return
    #   assert type(self.SOLR_URL) == str  # required
    #   ## load data
    #   json_dict = json.loads( self.file_data )
    #   # logger.debug( u'in Updater.post_to_solr(); sorted(json_dict.keys()) is: %s' % pprint.pformat( sorted(json_dict.keys()) ) )
    #   id_list = json_dict['id_list']
    #   fdd = json_dict['file_data']  # file_data_dict
    #   ## work
    #   sdl = []  # solr_dict_list
    #   for key in id_list:
    #     # logger.debug( u'in Updater.post_to_solr(); key is: %s' % key )
    #     ## build solr info
    #     try:
    #       sdl.append( fdd[key]['solr_data'] )
    #       # break  # for testing
    #     except Exception as e:
    #       logger.error( u'in Updater.post_to_solr(); exception on building solr_dict_list is: %s' % repr(e).decode(u'utf-8', u'replace') )
    #       logger.debug( u'above error prolly ok; prolly a bad file was skipped; key tried: %s' % key )
    #       pass
    #   ## post to solr
    #   # logger.debug( u'in Updater.post_to_solr(); about to post to solr' )
    #   try:
    #     s = solr.Solr( self.SOLR_URL )
    #     # s = solr.SolrConnection( self.SOLR_URL )
    #     response = s.add_many( sdl )
    #     s.commit()
    #     s.close()
    #     logger.debug( u'in Updater.post_to_solr(); post done; response is: %s' % response )
    #     # self.updateLog( {u'- in post_to_solr()': u'post done'} )
    #     # self.updateLog( {u'- in post_to_solr(); response': response} )
    #   except Exception as e:
    #     logger.debug( u'in Updater.post_to_solr(); exception on post is: %s' % repr(e).decode(u'utf-8', u'replace') )
    #   # end def post_to_solr()

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
