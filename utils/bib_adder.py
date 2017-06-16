# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, os, pprint
import requests
from lxml import etree


LOG_CONF_JSN = unicode( os.environ[u'usep_gh__WRKR_LOG_CONF_JSN'] )


log = logging.getLogger( 'usep_gh_worker_logger' )
if not logging._handlers:  # true when module accessed by queue-jobs
    logging_config_dct = json.loads( LOG_CONF_JSN )
    logging.config.dictConfig( logging_config_dct )


class BibAdder():
    """Adds hierarchical bibliography to a given inscription."""

    def __init__(self, solr_url, titles_url, log):
        self.solr_url = solr_url
        try:
            r = requests.get(titles_url)
            self.titles_xml = etree.fromstring(r.content)
        except Exception as e:
            log.error( 'Exception in __init__, ```%s```' % unicode(repr(e)) )
            raise Exception( unicode(repr(e)) )

    def addBibl(self, inscription_id):
        log.debug( 'addBibl inscription_id, `%s`' % inscription_id )
        log.debug( 'self.solr_url, ```%s```' % self.solr_url )
        try:
            # params = {'q':'id:"{}"'.format(inscription_id), 'fl':'bib_ids', 'wt':'json'}
            params = {'q':'id:"%s"' % inscription_id, 'fl':'bib_ids', 'wt':'json'}
            log.debug( 'params, ```%s```' % pprint.pformat(params) )
            r = requests.get( self.solr_url + "/select", params=params )
        except Exception, e:
            log.error( 'Exception on requests select, ```%s```' % unicode(repr(e)) )
            raise Exception( unicode(repr(e)) )

        try:
            doc = r.json()['response']['docs'][0]
            bib_ids = doc["bib_ids"] if "bib_ids" in doc else []
        except KeyError:
            log.error("KeyError: Solr returned no results for id: {}".format(inscription_id))
            return False

        ids = set()
        for i in bib_ids:
            ids.update(etree.XPath("//tei:bibl[@xml:id='"+i+"']/ancestor::tei:bibl/@xml:id", namespaces={"tei":"http://www.tei-c.org/ns/1.0"})(self.titles_xml))

        update_json = json.dumps([{"id":inscription_id, "bib_ids":{"add":list(ids)}}])
        log.debug("Updating {0} with JSON {1}".format(inscription_id, update_json))

        try:
            p = requests.post(self.solr_url + "/update", data=update_json, headers={'Content-type':'application/json'})
            r = requests.get(self.solr_url + "/update?softCommit=true")
            return True
        except Exception, e:
            log.error( 'Exception on requests post or followup get, ```%s```' % unicode(repr(e)) )
            raise Exception( unicode(repr(e)) )

    # end class BibAdder
