# -*- coding: utf-8 -*-

import json, logging, os, pprint
import lxml, redis, requests, rq, solr
from lxml import etree
from usep_gh_handler_app.utils import bib_adder, log_helper


# LOG_CONF_JSN = unicode( os.environ[u'usep_gh__WRKR_LOG_CONF_JSN'] )
# log = logging.getLogger( 'usep_gh_worker_logger' )
# if not logging._handlers:  # true when module accessed by queue-jobs
#     logging_config_dct = json.loads( LOG_CONF_JSN )
#     logging.config.dictConfig( logging_config_dct )
# log.debug( 'indexer logging ready' )


LOG_CONF_JSN = os.environ[u'usep_gh__WRKR_LOG_CONF_JSN']
logging_config_dct = json.loads( LOG_CONF_JSN )
log = logging.getLogger( 'usep_gh_worker_logger' )
logging.config.dictConfig( logging_config_dct )
log.debug( 'indexer logging ready' )


class Indexer( object ):
    """ Contains functions for hitting solr.
        TODO: Refactor so the index-removal can take ids instead of filenames.
              That way, it can be called from the reindex-all code, too. """

    def __init__( self ):
        """ Settings. """
        self.worthwhile_dirs = [ u'bib_only', u'metadata_only', u'transcribed' ]  # only need to update index for these dirs
        self.WEBSERVED_DATA_DIR_PATH = os.environ.get(u'usep_gh__WEBSERVED_DATA_DIR_PATH')
        self.SOLR_URL = os.environ.get(u'usep_gh__SOLR_URL')
        self.SOLR_XSL_PATH = os.environ.get(u'usep_gh__SOLR_XSL_PATH')
        self.TITLES_URL = os.environ.get(u'usep_gh__TITLES_URL')
        self.TRANSCRIPTION_PARSER_XSL_PATH = os.environ.get('usep_gh__TRANSCRIPTION_PARSER_XSL_PATH')

    ## update index entry ##

    def update_index_entry( self, filename ):
        """ Updates solr index for a new or changed file.
            Called by run_update_index() """
        log.debug( u'in utils.indexer.update_index_entry(); filename, `%s`' % filename )
        full_file_path = u'%s/inscriptions/%s' % ( self.WEBSERVED_DATA_DIR_PATH, filename )
        transformed_xml_txt = self._build_solr_doc( full_file_path )
        resp = self._post_solr_update( transformed_xml_txt )
        log.debug( 'post response, ```%s```' % resp )
        self._update_bib( filename )
        # self._update_transcription( filename )
        return

    def _build_solr_doc( self, inscription_xml_path ):
        """ Builds solr doc.
            Called by update_index_entry() """
        log.debug( 'inscription_xml_path, ```%s```' % inscription_xml_path )
        log.debug( 'self.SOLR_XSL_PATH, ```%s```' % self.SOLR_XSL_PATH )
        with open( inscription_xml_path ) as f:
            xml_txt = f.read()
        with open( self.SOLR_XSL_PATH ) as f:
            xsl_txt = f.read()
        xml_dom_obj = etree.fromstring( xml_txt.encode('utf-8') )
        transformer_obj = etree.XSLT( etree.fromstring(xsl_txt.encode('utf-8')) )
        transformed_xml_dom_obj = transformer_obj( xml_dom_obj )
        transformed_xml_utf8 = etree.tostring( transformed_xml_dom_obj, pretty_print=True )
        transformed_xml_txt = transformed_xml_utf8.decode( 'utf-8' )
        log.debug( 'transformed_xml_txt, ```%s```' % transformed_xml_txt )
        return transformed_xml_txt

    def _post_solr_update( self, solr_xml ):
        """ Posts solr doc.
            Called by update_index_entry() """
        log.debug( 'self.SOLR_URL, ```%s```' % self.SOLR_URL )
        try:
            r = requests.post(
                self.SOLR_URL + u"/update",
                data=solr_xml,
                headers={"Content-type":"application/xml"},
                timeout=30
                )
            resp = r.content.decode( 'utf-8' )
            log.debug( 'post resp, ```%s```' % resp )
        except Exception as e:
            log.error( 'Exception, ```%s```' % unicode(repr(e)) )
            raise Exception( unicode(repr(e)) )
        return resp

    def _update_bib( self, filename ):
        """ Updates bib data for inscription.
            Called by update_index_entry() """
        try:
            ## make id
            inscription_id = filename.strip().split(u'.xml')[0]
            ## call bib-adder
            bibber = bib_adder.BibAdder( self.SOLR_URL, self.TITLES_URL )
            result = bibber.addBibl( inscription_id )
            ## log response
            log.debug( 'addBibl response, `%s`' % result )
        except Exception as e:
            log.error( 'exception updating bib, ```%s```' % unicode(repr(e)) )
        return

    def _update_transcription( self, filename ):
        """ Updates transcription info for inscription.
            Called by update_index_entry() """
        try:
            ## make id
            inscription_id = filename.strip().split(u'.xml')[0]
            ## call transcription_adder
            transcriptor = transcription_adder.TranscriptionAdder( self.SOLR_URL, self.TRANSCRIPTION_PARSER_XSL_PATH )
            result = transcriptor.add_transcription( inscription_id )
            ## log response
            log.debug( 'add_transcription response, `%s`' % result )
        except Exception as e:
            log.error( 'exception updating transcription info, ```%s```' % unicode(repr(e)) )
        return

    ## remove index entry ##

    def remove_index_entry( self, filename=None, inscription_id=None ):
        """ Updates solr index for a removed file. """
        if filename:
            inscription_id = filename.strip().split(u'.xml')[0]
        log.debug( u'in utils.indexer.Indexer.remove_index_entry(); filename, `%s`; inscription_id, `%s`' % (filename, inscription_id) )
        s = solr.Solr( self.SOLR_URL )
        response = s.delete( id=inscription_id )
        s.commit()
        s.close()
        log.debug( u'in utils.indexer.Indexer.remove_index_entry(); post complete; response is: %s' % response )
        return

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
        Triggered by utils.processor.run_xinclude_updater(). """
    indexer = Indexer()
    for removed_file_path in files_removed:
        if indexer.check_removed_file_path( removed_file_path ):
            q.enqueue_call(
                func=u'usep_gh_handler_app.utils.indexer.run_remove_entry', kwargs={u'removed_file_path': removed_file_path} )
    for updated_file_path in files_updated:
        if indexer.check_updated_file_path( updated_file_path ):
            q.enqueue_call(
                func=u'usep_gh_handler_app.utils.indexer.run_update_entry', kwargs={u'updated_file_path': updated_file_path} )
    return

def run_update_entry( updated_file_path ):
    """ Updates solr index for a new or changed file.
        Triggered by run_update_index(), and utils.reindex_all_support.run_enqueue_all_index_updates(). """
    indexer = Indexer()
    filename = updated_file_path.split( u'/' )[-1]
    indexer.update_index_entry( filename )
    return

def run_remove_entry( removed_file_path ):
    """ Updates solr index for removed file.
        Triggered by run_update_index(). """
    indexer = Indexer()
    filename = removed_file_path.split( u'/' )[-1]
    indexer.remove_index_entry( filename=filename )
    return

def run_remove_entry_via_id( id_to_remove ):
    """ Removes id from solr.
        Triggered by utils.reindex_all_support.run_enqueue_all_index_updates(). """
    indexer = Indexer()
    indexer.remove_index_entry( inscription_id=id_to_remove )
    return
