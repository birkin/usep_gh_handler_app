# -*- coding: utf-8 -*-

import json, logging, os, re
import requests
from lxml import etree


LOG_CONF_JSN = unicode( os.environ[u'usep_gh__WRKR_LOG_CONF_JSN'] )


log = logging.getLogger( 'usep_gh_worker_logger' )
if not logging._handlers:  # true when module accessed by queue-jobs
    logging_config_dct = json.loads( LOG_CONF_JSN )
    logging.config.dictConfig( logging_config_dct )



class TranscriptionAdder( object ):
    """ Adds a 'transcription' field in Solr to inscriptions which have one"""

    def __init__( self, solr_url, xsl_path ):
        log.debug( 'initializing TranscriptionAdder' )
        self.solr_url = solr_url
        self.lb_whitespace = re.compile(r"(<lb.*/>)\s+(.*)")
        self.transform = None
        try:
            with open( xsl_path, 'r' ) as f:
                utf8_xsl_text = f.read()
                self.transform = etree.XSLT( etree.fromstring(utf8_xsl_text) )
        except Exception as e:
            log.error( 'Exception in __init__, ```%s```' % unicode(repr(e)) )
            raise Exception( unicode(repr(e)) )

    def add_transcription(self, inscription_id, xml_path):
        """ Manages preparation, and posts a solr update of transcription info.
            Called by utils/indexer/Indexer._update_transcription() """
        transcription = str( self.index_value(xml_path) )
        solr_req_text = json.dumps({
            "add": {
                "doc": {
                    "id":inscription_id,
                    "transcription":{"set":transcription}
                    }
                }
            })
        try:
            p = requests.post( self.solr_url+"/update", data=solr_req_text, headers={"Content-type":"application/json"}, timeout=30 )
            g = requests.get( self.solr_url+"/update?softCommit=true", timeout=30 )
        except Exception as e:
            log.error( 'Exception in add_transcription(), ```%s```' % unicode(repr(e)) )
            raise e

    def index_value(self, xml_path):
        """ Calls munger on transcription text, creates transcription doc, and calls transformer.
            Called by add_transcription() """
        t = self.munge_transcription( xml_path )
        xml = etree.fromstring(t)
        transformed_xml = self.transform( xml )
        return transformed_xml

    def munge_transcription( self, xml_path ):
        """ Extracts, munges and returns transcription data.
            Called by index_value() """
        with open( xml_path, "r" ) as f:
            xml = etree.fromstring( f.read() )
            elts = xml.xpath("//tei:div[@type='edition']/tei:ab", namespaces={"tei":"http://www.tei-c.org/ns/1.0"})
            munged = ""
            for e in elts:
                content = etree.tostring(e)
                lines = [l.strip() for l in content.split("\n")]
                for l in lines:
                    m = self.lb_whitespace.match(l)
                    if m:
                        l = m.groups()[0] + m.groups()[1]
                    munged += l
            return munged

    # end class TranscriptionAdder()
