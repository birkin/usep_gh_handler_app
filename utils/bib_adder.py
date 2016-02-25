# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import requests
import json
from lxml import etree


class BibAdder():
	"""Adds hierarchical bibliography to a given inscription."""

	def __init__(self, solr_url, titles_url, log):
		self.solr_url = solr_url
		self.log = log

		try:
			r = requests.get(titles_url)
			self.titles_xml = etree.fromstring(r.content)
		except Exception as e:
			self.log.error( 'Exception, ```%s```' % unicode(repr(e)) )
			raise Exception( unicode(repr(e)) )

	def addBibl(self, inscription_id):
		try:
			r = requests.get(self.solr_url + "/select", params={'q':'id:"{}"'.format(inscription_id), 'fl':'bib_ids', 'wt':'json'})
		except Exception, e:
			self.log.error( 'Exception, ```%s```' % unicode(repr(e)) )
			raise Exception( unicode(repr(e)) )

		try:
			doc = r.json()['response']['docs'][0]
			bib_ids = doc["bib_ids"] if "bib_ids" in doc else []
		except KeyError:
			self.log.error("KeyError: Solr returned no results for id: {}".format(inscription_id))
			return False

		ids = set()
		for i in bib_ids:
			ids.update(etree.XPath("//tei:bibl[@xml:id='"+i+"']/ancestor::tei:bibl/@xml:id", namespaces={"tei":"http://www.tei-c.org/ns/1.0"})(self.titles_xml))

		update_json = json.dumps([{"id":inscription_id, "bib_ids":{"add":list(ids)}}])
		self.log.debug("Updating {0} with JSON {1}".format(inscription_id, update_json))

		try:
			p = requests.post(self.solr_url + "/update", data=update_json, headers={'Content-type':'application/json'})
			r = requests.get(self.solr_url + "/update?softCommit=true")
			return True
		except Exception, e:
			self.log.error( 'Exception, ```%s```' % unicode(repr(e)) )
			raise Exception( unicode(repr(e)) )

    # end class BibAdder
