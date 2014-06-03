# -*- coding: utf-8 -*-

import lxml
from lxml import etree


class Parser( object ):
  """ Contains functions for preparing solr-data.
      TODO: replace pq extracts with straight lxml or beautifulsoup extracts. """

  def __init__( self, inscription_xml_path, bib_xml_path, log ):
    '''
    - makes lxml-doc from xml_path
    - if bib_xml_path:
      - makes lxml-bib-doc from bib_xml
      - makes lxml-docs of matching bib_xml elements for future author/title/etc parsing
    - sets some attributes
    '''
    self.log = log
    ## attributes
    self.bib_authors = None  # from parseBibAuthors()
    self.bib_doc = None  # from init(); lxml-object from bib-xml
    self.bib_docs = None  # from init(); list of lxml-docs for bib_id matches
    self.bib_ids = None  # from makeBibDocs(); from inscription-xml
    self.bib_ids_filtered = None  # from parseBibIdsFiltered()
    self.bib_ids_types = None
    self.bib_titles = None  # from parseBibTitles() -- no duplicates
    self.bib_titles_all = None  # from parseBibTitles() -- includes duplicates (for bib-type matching)
    self.bib_xml_path = bib_xml_path  # passed in; optional
    self.bib_xml = None  # from init()
    self.condition = None
    self.decoration = None
    self.parse_errors = None  # will be unicode string on error
    self.fake = None
    self.i_id = None  # from parseId()
    self.graphic_name = None
    self.language = None
    # self.log = []
    self.material = None
    self.msid_region = None  # msid attributes listed in logical order
    self.msid_settlement = None
    self.msid_repository = None
    self.msid_institution = None
    self.msid_idno = None
    self.namespace = { u't': u'http://www.tei-c.org/ns/1.0' }
    self.status = None  # one of [ bib_only, metadata, transcription ]
    self.title = None
    self.writing = None
    self.xml = None  # from init()
    self.xml_doc = None  # from init()
    self.xml_path = inscription_xml_path  # passed in; required
    ## standard work
    self.loadAndDocifyInscriptionXml()
    self.parseId()
    self.loadAndDocifyBiblXml()  # requires self.bib_xml_path
    self.makeBibDocs()  # requires self.bib_doc, set by self.loadAndDocifyBiblXml()
    # self.log.debug( u'end of Parser.__init__()' )

  def loadAndDocifyInscriptionXml(self):
    """Makes an lxml object from the inscription file."""
    assert type(self.xml_path) == unicode, Exception( u'type(self.xml_path) should be unicode; it is: %s' % type(self.xml_path) )
    self.xml = open( self.xml_path ).read().decode( u'utf-8' )
    assert type(self.xml) == unicode, Exception( u'type(self.xml) should be unicode; it is: %s' % type(self.xml) )
    try:
      self.xml_doc = etree.fromstring( self.xml.encode(u'utf-8') )  # str required because xml contains an encoding declaration
    except lxml.etree.XMLSyntaxError, e:
      log.error( u'in Parser.loadAndDocifyInscriptionXml(); error instantiating xml_doc; xml_path is: %s; e is: %s' % (self.xml_path, repr(e).decode(u'utf-8', u'replace')) )
      self.parse_errors = u'in Parser.loadAndDocifyInscriptionXml(); unable to load xml string into an xml doc'

  def loadAndDocifyBiblXml(self):
    if self.parse_errors: return
    try:
      if self.bib_xml_path:
        assert type(self.bib_xml_path) == unicode, Exception( u'type(self.bib_xml_path) should be unicode; it is: %s' % type(self.bib_xml_path) )
        self.bib_xml = open( self.bib_xml_path ).read().decode(u'utf-8')
        assert type(self.bib_xml) == unicode, Exception( u'type(self.bib_xml) should be unicode; it is: %s' % type(self.bib_xml) )
        self.bib_doc = etree.fromstring( self.bib_xml.encode(u'utf-8') )  # str required because bib_xml contains an encoding declaration
        assert unicode(type(self.bib_doc)) == u"<type 'lxml.etree._Element'>", Exception( u'type(self.bib_doc) should be lxml.etree._Element; it is: %s' % unicode(type(self.bib_doc)) )
        return self.bib_doc
    except Exception as e:
      log.error( u'in Parser.loadAndDocifyBiblXml(); exception e is: %s' % repr(e).decode(u'utf-8', u'replace') )
      self.parse_errors = u'in Parser.loadAndDocifyBiblXml(); unable to load expected bib doc'

  def makeBibDocs(self):
    """If there's a bib-doc, this examines it & populates self.bib_docs for various bib-parsing defs"""
    if self.parse_errors: return
    try:
      if not self.bib_doc == None:
        if self.bib_ids == None:
          # self.log.debug( u'in makeBibDocs(); about to call parseBibIds()' )
          self.parseBibIds()
        if len( self.bib_ids ) == 0:
          self.bib_docs = []
          self.bib_titles = []
          self.bib_authors = []
          # return self.bib_docs
        else:
          self.bib_docs = []
          for bib_id in self.bib_ids:
            self.log.debug( u'in makeBibDocs(); about to make bib-doc for bib_id: %s' % bib_id )
            ## find bib-match (in bib xml)
            found_el = None
            for el in self.bib_doc.iter( u'{http://www.tei-c.org/ns/1.0}bibl' ):
              if el.attrib[ u'{http://www.w3.org/XML/1998/namespace}id' ] == bib_id:
                found_el = el
                self.log.debug( u'in makeBibDocs(); bib-doc found: %s' % etree.tostring(found_el) )
                self.bib_docs.append( found_el )
                break
            if found_el == None:
              self.log.debug( u'in makeBibDocs(); NO bib-doc found' )
              self.bib_docs.append( None )
        self.log.debug( u'in makeBibDocs(); self.bib_docs: %s' % self.bib_docs )
        return self.bib_docs
      else:
        return
    except Exception as e:
      # self.parse_errors = u'exception in makeBibDocs() is: %s' % repr(e).decode(u'utf-8', u'replace')
      message = u'makeBibDocs() exception is: %s' % repr(e).decode(u'utf-8', u'replace')
      self.log.error( message )
      self.parse_errors = u'in Parser.makeBibDocs(); problem making bib-docs; error logged'

  def parseBibAuthors(self):
    try:
      if self.parse_errors: return
      assert type(self.bib_docs) == list
      bib_authors = []
      for bib_match_element in self.bib_docs:
        if bib_match_element == None:
          bib_authors.append( u'unknown' )
        # print etree.tostring( bib_match_element )
        elif unicode( bib_match_element.attrib[u'type'] ) == u'm':  # monograph
          bib_authors = self._parse_bib_authors_from_monograph( bib_match_element, bib_authors )
        elif unicode( bib_match_element.attrib[u'type'] ) == u'v':  # volume -- for now, handle same as monograph, though this may change
          bib_authors = self._parse_bib_authors_from_volume( bib_match_element, bib_authors )
      cleaned_authors = self._clean_list_entries( bib_authors )
      self.bib_authors = cleaned_authors
      return self.bib_authors
    except Exception as e:
      message = u'parseBibAuthors() exception is: %s' % repr(e).decode(u'utf-8', u'replace')
      log.error( message )
      self.parse_errors = u'in Parser.parseBibAuthors(); problem parsing bib-authors'

  def _parse_bib_authors_from_monograph( self, bib_match_element, bib_authors ):
    """ Returns list of bib_authors.
        Called by parseBibAuthors() """
    author_docs = []
    for el in bib_match_element.iterchildren():  # get author elements
      if unicode(el.tag) == u'{http://www.tei-c.org/ns/1.0}author':
        author_docs.append( el )
    for author_doc in author_docs:
      for child in author_doc.iterchildren():  # get author name
        if unicode(child.tag) == u'{http://www.tei-c.org/ns/1.0}persName' and child.attrib == {u'type': u'sort'}:  # if child.attrib == {}, that's the plain name
          bib_authors.append( child.text.decode(u'utf-8') ) if type(child.text) == str else bib_authors.append( child.text )
    return bib_authors

  def _parse_bib_authors_from_volume( self, bib_match_element, bib_authors ):
    """ Returns list of bib_authors.
        Called by parseBibAuthors()
        For now the same as parsing a monograph; may change in future. """
    bib_authors = self._parse_bib_authors_from_monograph( bib_match_element, bib_authors )
    return bib_authors

  def _clean_list_entries( self, list_entries ):
    """ Returns list with unnecessary multiple spaces and newlines removed from entries.
        Called by parseBibAuthors(), parseBibTitles() """
    cleaned_entries = []
    for entry in list_entries:
      if entry == None:
        continue
      cleaned_entry = u' '.join( entry.split() )
      cleaned_entries.append( cleaned_entry )
    return cleaned_entries

  def parseBibIds(self):
    """Called by makeBibDocs() when there's bib info."""
    if self.parse_errors: return
    self.bib_ids = []
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:listBibl/t:bibl/t:ptr'
    NS = { 't': 'http://www.tei-c.org/ns/1.0' }
    elements = self.xml_doc.xpath( xpath, namespaces=(NS) )
    for bib in elements:
      if bib.attrib[u'type'].decode(u'utf-8') == u'rest-of-bibl':  # found one that's type="edh"
        bib_text = None
        try:
          bib_text = bib.attrib[u'target'].split(u'#')[1]
        except IndexError, e:
          self.log.debug( u'in Parser.parseBibIds(); error on file: %s; error (possibly missing hash): %s' % (self.xml_path, repr(e).decode(u'utf-8', u'replace')) )
          pass
        if bib_text:
          assert type(bib_text) == unicode, Exception( u'in parseBibIds(); type(bib_text) should be unicode; it is: %s' % type(bib_text) )
          self.bib_ids.append( bib_text )
    self.bib_ids = sorted( self.bib_ids )
    # self.log.debug( u'in parseBibIds(); self.bib_ids is: %s' % self.bib_ids )
    if self.bib_ids == []:
      self.parse_errors = u'in Parser.parseBibIds(); expected bib_ids; none found'
      self.log.debug( u'in parseBibIds(); setting self.parse_errors because self.bib_ids is empty.' )
    self.log.debug( u'in parseBibIds(); self.bib_ids is: %s' % self.bib_ids )
    return self.bib_ids

  def parseBibIdsFiltered(self):
    if self.parse_errors: return
    ancestor_ids_filtered = []
    if self.bib_docs == None:
      self.makeBibDocs()
    assert type(self.bib_docs) == list, Exception( u'in parseBibIdsFiltered(); type(self.bib_docs) should be list; it is: %s' % type(self.bib_docs) )
    for bib_doc in self.bib_docs:  ## access the xml element
      if bib_doc == None:
        ancestor_ids_filtered.append( u'unknown' )
      else:
        assert type(self.bib_doc) == lxml.etree._Element, Exception( u'in parseBibIdsFiltered(); type(self.bib_doc) should be lxml.etree._Element; it is: %s' %  type(self.bib_doc) )
        ## get id
        doc_id = bib_doc.attrib[u'{http://www.w3.org/XML/1998/namespace}id']
        has_parent = True
        ## see if we're already at the top level
        if bib_doc.attrib[u'type'] in [u'c', u'j']:
          filtered_id = bib_doc.attrib[u'{http://www.w3.org/XML/1998/namespace}id'].decode(u'utf-8')
          if not filtered_id in ancestor_ids_filtered:
            ancestor_ids_filtered.append( filtered_id )
        else: ## else... travel up to the top bibl ancestor
          ancestors = []
          for ancestor in bib_doc.iterancestors():
            if ancestor.tag == u"{http://www.tei-c.org/ns/1.0}bibl":
              ancestors.append( ancestor )
            else:  # we're at the top bibl
              break
          ## examine top bibl ancestor
          ancestor = ( ancestors[-1:][0] if len(ancestors) > 0 else None )
          if not ancestor == None:
            ancestor_id = ancestor.attrib[u'{http://www.w3.org/XML/1998/namespace}id']
            ## add it to the ultimate list
            if ancestor.attrib[u'type'] in [u'c', u'j']:
              filtered_id = ancestor.attrib[u'{http://www.w3.org/XML/1998/namespace}id'].decode(u'utf-8')
              if not filtered_id in ancestor_ids_filtered:
                ancestor_ids_filtered.append( filtered_id )
    ## update attribute & return
    self.bib_ids_filtered = ancestor_ids_filtered
    return self.bib_ids_filtered

  def parseBibIdsTypes(self):
    if self.parse_errors: return
    bib_ids_types = []
    if self.bib_docs == None:
      self.makeBibDocs()
    assert type(self.bib_docs) == list, type(self.bib_docs)
    for bib_doc in self.bib_docs:  ## access the xml element
      if bib_doc == None:
        bib_ids_types.append( u'unknown' )
      else:
        assert type(self.bib_doc) == lxml.etree._Element, type(self.bib_doc)
        ## get id
        doc_id = bib_doc.attrib[u'{http://www.w3.org/XML/1998/namespace}id']
        # has_parent = True  # i think i can get rid of this
        ## see if we're already at the top level
        if bib_doc.attrib[u'type'] in [u'c', u'j', u'm']:
          if bib_doc.attrib[u'type'] == u'c':
            bib_ids_types.append( u'corpora' )
          elif bib_doc.attrib[u'type'] == u'j':
            bib_ids_types.append( u'journal' )
          elif bib_doc.attrib[u'type'] == u'm':
            bib_ids_types.append( u'monograph' )
        else: ## else... travel up to the top bibl ancestor
          ancestors = []
          for ancestor in bib_doc.iterancestors():
            if ancestor.tag == u"{http://www.tei-c.org/ns/1.0}bibl":
              ancestors.append( ancestor )
            else:  # we're at the top bibl
              break
          ## examine top bibl ancestor
          ancestor = ( ancestors[-1:][0] if len(ancestors) > 0 else None )
          if not ancestor == None:
            ancestor_id = ancestor.attrib[u'{http://www.w3.org/XML/1998/namespace}id']
            ## add it to the ultimate list
            if ancestor.attrib[u'type'] == u'c':
              bib_ids_types.append( u'corpora' )
            elif ancestor.attrib[u'type'] == u'j':
              bib_ids_types.append( u'journal' )
    ## update attribute & return
    self.bib_ids_types = bib_ids_types
    return self.bib_ids_types

  def parseBibTitles(self):
    """ Parses bib titles from self.bib_docs """
    try:
      self._setup_bib_titles_work()
      for bib_match_element in self.bib_docs:
        if bib_match_element == None:  # in rare temporary case a bib_id may not have a corresponding <bibl> node
          title = u'unknown'
        elif unicode( bib_match_element.attrib[u'type'] ) in [u'c', u'j', u'm', u'u']:  # corpora, journal, monograph, unpublished?
          title = self._parse_bib_titles_from_nonvolume( bib_match_element )
        else:  # volume or non-standard match, so run up hierarchy
          title = self._parse_bib_titles_from_volume( bib_match_element )
        self._run_bib_title_appends( title )
      self._clean_bib_titles()
      return { u'bib_titles': self.bib_titles, u'bib_titles_all':self.bib_titles_all }
    except Exception as e:
      self.log.debug( u'in Parser.parseBibTitles(); exception is: %s' % repr(e).decode(u'utf-8', u'replace') )
      self.parse_errors = u'in Parser.parseBibTitles(); unable to parse expected bib-titles'

  def _setup_bib_titles_work( self ):
    """ Runs parseBibTitles() validation and initialization prep. """
    assert self.parse_errors == None
    assert type(self.bib_docs) == list
    self.bib_titles = []
    self.bib_titles_all = []
    return

  def _parse_bib_titles_from_nonvolume( self, target_element ):
    """ Returns list of bib-titles from non-volume.
        Called by parseBibTitles() """
    ## use element directly & extract title
    title = None
    for el in target_element.iterchildren():
      if unicode( el.tag ) == u'{http://www.tei-c.org/ns/1.0}title':
        title = el.text.decode(u'utf-8') if type(el.text) == str else el.text
        assert type(title) == unicode, type(title)
        break
    assert title
    return title

  def _parse_bib_titles_from_volume( self, target_element ):
    """ Returns list of bib-titles from volume.
        Called by parseBibTitles() """
    flag = True
    while flag == True:
      target_element = target_element.getparent()
      for el in target_element.iterchildren():  # check current element for title
        if unicode( el.tag ) == u'{http://www.tei-c.org/ns/1.0}title':
          title = el.text.decode(u'utf-8') if ( type(el.text) == str ) else el.text
          assert type(title) == unicode, type(title)
          flag = False
          break
    assert title
    return title

  def _run_bib_title_appends( self, title ):
    """ Updates attributes. """
    self.bib_titles_all.append( title )
    if not title in self.bib_titles:
      self.bib_titles.append( title )
    return

  def _clean_bib_titles( self ):
    """ Cleans spaces and returns. """
    self.bib_titles = self._clean_list_entries( self.bib_titles )
    self.bib_titles_all = self._clean_list_entries( self.bib_titles_all )
    return

  def parseCondition(self):
    if self.parse_errors: return
    NS = {'t': 'http://www.tei-c.org/ns/1.0'}
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:physDesc/t:objectDesc/t:supportDesc/t:condition'
    # xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:msContents/t:textLang'
    element_list = self.xml_doc.xpath( xpath, namespaces=(NS) )
    if len( element_list ) > 0:
      element = element_list[0]
      assert type(element) == lxml.etree._Element, type(element)
      try:
        x = element.attrib[u'ana']
      except KeyError:
        return self.condition  # None
      x = x.decode( u'utf-8' )
      x = ( x[1:] if x[0] == u'#' else x )
      assert type(x) == unicode, type(x)
      self.condition = x
      return self.condition

  def parseDecoration(self):
    if self.parse_errors: return
    NS = {'t': 'http://www.tei-c.org/ns/1.0'}
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:physDesc/t:decoDesc/t:decoNote'
    element_list = self.xml_doc.xpath( xpath, namespaces=(NS) )
    if len( element_list ) > 0:
      element = element_list[0]
      assert type(element) == lxml.etree._Element, type(element)
      try:
        x = element.attrib[u'ana']
      except KeyError:
        return self.decoration  # None
      x = x.decode( u'utf-8' )
      x = ( x[1:] if x[0] == u'#' else x )
      assert type(x) == unicode, type(x)
      self.decoration = x
      return self.decoration

  def parseFake(self):
    if self.parse_errors: return
    NS = {'t': 'http://www.tei-c.org/ns/1.0'}
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:history/t:summary/t:rs'
    element_list = self.xml_doc.xpath( xpath, namespaces=(NS) )
    if len( element_list ) > 0:
      element = element_list[0]
      assert type(element) == lxml.etree._Element, type(element)
      x = element.text
      try:
        x = x.decode( u'utf-8' )
        assert type(x) == unicode, type(x)
        self.fake = x
      except AttributeError:  # empty element fails on None.decode()
        pass  # leave self.fake in None-initialized state
      return self.fake

  def parseId(self):
    if self.parse_errors: return
    try:
      xpath = u't:teiHeader/t:fileDesc/t:publicationStmt/t:idno'
      NS = {'t': 'http://www.tei-c.org/ns/1.0'}
      element = self.xml_doc.xpath( xpath, namespaces=(NS) )[0]
      assert unicode(type(element)) == u"<type 'lxml.etree._Element'>"
      i_id = element.attrib[u'{http://www.w3.org/XML/1998/namespace}id']
      self.i_id = i_id.decode( u'utf-8' )
      assert type(self.i_id) == unicode
      # self.log.debug( u'in Parser.parseId(); created i_id is: %s' % self.i_id )
      return self.i_id
    except Exception as e:
      log.error( u'in Parser.parseId(); exception is: %s' % repr(e).decode(u'utf-8', u'replace') )
      self.parse_errors = u'parseId() exception is: %s' % repr(e).decode(u'utf-8', u'replace')

  def parse_graphic_name( self ):
    if self.parse_errors: return
    xpath = u't:facsimile/t:surface/t:graphic'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    if len( element_list ) > 0:
      element = element_list[0]
      graphic_name = element.attrib[u'url']
      graphic_name = graphic_name.decode( u'utf-8' ); assert type(graphic_name) == unicode, type(graphic_name)
      graphic_name = graphic_name.split( u' ' )[0]  # handles case: u'MI.AA.UM.KM.L.1019bis.jpg MI.AA.UM.KM.L.1019bis-Det.1.jpg'
      if len( graphic_name ) > 0:  # handles case of graphic element with empty url attribute
        self.graphic_name = graphic_name
    return self.graphic_name

  def parseLanguage(self):
    if self.parse_errors: return
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:msContents/t:textLang'
    NS = {'t': 'http://www.tei-c.org/ns/1.0'}
    element_list = self.xml_doc.xpath( xpath, namespaces=(NS) )
    if len( element_list ) > 0:
      element = element_list[0]
      assert type(element) == lxml.etree._Element, type(element)
      lang = element.attrib[u'mainLang']
      lang = lang.decode( u'utf-8' )
      assert type(lang) == unicode, type(lang)
      self.language = lang
      return self.language

  def parseMaterial(self):
    if self.parse_errors: return
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:physDesc/t:objectDesc/t:supportDesc'
    NS = {'t': 'http://www.tei-c.org/ns/1.0'}
    element_list = self.xml_doc.xpath( xpath, namespaces=(NS) )
    if len( element_list ) > 0:
      element = element_list[0]
      assert type(element) == lxml.etree._Element, type(element)
      material = element.attrib[u'ana']
      assert type(material) == str, type(material)
      material = material.decode( u'utf-8' )
      material = ( material[1:] if material[0] == u'#' else material )
      assert type(material) == unicode, type(material)
      self.material = material
      return self.material

  def parseMsidRegion(self):
    if self.parse_errors: return
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:msIdentifier/t:region'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    x = element_list[0].text
    if isinstance(x, str):
      self.msid_region = x.decode(u'utf-8', u'replace')
    return self.msid_region

  def parseMsidSettlement(self):
    if self.parse_errors: return
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:msIdentifier/t:settlement'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    x = element_list[0].text
    if isinstance(x, str):
      self.msid_settlement = x.decode(u'utf-8', u'replace')
    return self.msid_settlement

  def parseMsidInstitution(self):
    if self.parse_errors: return
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:msIdentifier/t:institution'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    x = element_list[0].text
    if isinstance(x, str):
      self.msid_institution = x.decode(u'utf-8', u'replace')
    return self.msid_institution

  def parseMsidRepository(self):
    if self.parse_errors: return
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:msIdentifier/t:repository'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    x = element_list[0].text
    if isinstance(x, str):
      self.msid_repository = x.decode(u'utf-8', u'replace')
    return self.msid_repository

  def parseMsidIdno(self):
    if self.parse_errors: return
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:msIdentifier/t:idno'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    x = element_list[0].text
    if isinstance(x, str):
      self.msid_idno = x.decode(u'utf-8', u'replace')
    return self.msid_idno

  def parseStatus(self):
    if self.parse_errors: return
    ## bib only check
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:physDesc'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    el = element_list[0]
    children = list( el )
    if len( children ) == 0:
      self.status = u'bib_only'
    elif len( children ) == 1 and type( children[0] == lxml.etree._Comment ):
      self.status = u'bib_only'
    if not self.status == None:
      return self.status
    ## transcription check
    xpath = u't:text/t:body/t:div/t:ab'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    if len( element_list ) == 1:
      self.status = u'transcription'
    else:
      self.status = u'metadata'
    return self.status






  # def parse_text_genre( self ):
  #   """ Parses class from msItem element.
  #       Example: grabs 'verse' from <msItem class="#verse">
  #       Called by utils.indexer.Indexer._build_solr_dict()
  #       TODO: refactor to remove pyquery dependency. """
  #   from pyquery import PyQuery
  #   xml = open( self.xml_path ).read()
  #   d_xml = xml.replace( 'xmlns:', 'xmlnamespace:' )  # de-namespacing for easy element addressing
  #   pyquery_object = PyQuery( d_xml )  # pq is now addressable w/jquery syntax
  #   text_genre = []  # multi-valued
  #   tg_segments = pyquery_object('msitem').attr('class')
  #   if tg_segments:
  #     tg_segments = tg_segments.split()
  #     for tg_entry in tg_segments:
  #       tg_entry = tg_entry.strip()
  #       if tg_entry[0] == '#':
  #         tg_entry = tg_entry[1:]
  #       text_genre.append( tg_entry )
  #   if len( text_genre ) > 0:
  #     return_val = text_genre
  #   else:
  #     return_val = None
  #   return return_val

  def parse_text_genre( self ):
    """ Parses class from msItem element.
        Example: grabs 'verse' from <msItem class="#verse">
        Called by utils.indexer.Indexer._build_solr_dict()
        TODO: refactor to remove pyquery dependency. """
    from pyquery import PyQuery
    xml = open( self.xml_path ).read().decode(u'utf-8')
    d_xml = xml.replace( u'xmlns:', u'xmlnamespace:' )  # de-namespacing for easy element addressing
    pyquery_object = PyQuery( d_xml.encode(u'utf-8') )  # PyQuery requires bytes; is now addressable w/jquery syntax
    text_genre = []  # multi-valued
    tg_segments = pyquery_object(u'msitem').attr(u'class')
    if tg_segments:
      tg_segments = tg_segments.split()
      for tg_entry in tg_segments:
        # tg_entry = tg_entry.strip()
        tg_entry = tg_entry.decode(u'utf-8').strip()
        if tg_entry[0] == u'#':
          tg_entry = tg_entry[1:]
        text_genre.append( tg_entry )
    if len( text_genre ) > 0:
      return_val = text_genre
    else:
      return_val = None
    return return_val

  def parse_object_type( self ):
    """ Parses object_type.
        Called by utils.indexer.Indexer._build_solr_dict()
        TODO: refactor to remove pyquery dependency. """
    from pyquery import PyQuery
    xml = open( self.xml_path ).read().decode(u'utf-8')
    d_xml = xml.replace( u'xmlns:', u'xmlnamespace:' )  # de-namespacing for easy element addressing
    pyquery_object = PyQuery( d_xml.encode(u'utf-8') )  # PyQuery requires bytes; is now addressable w/jquery syntax
    object_type = []
    ot_segments = pyquery_object('objectdesc').attr('ana')
    if ot_segments:
      ot_segments = ot_segments.split()
      for ot_entry in ot_segments:
        # ot_entry = ot_entry.strip()
        ot_entry = ot_entry.decode(u'utf-8').strip()
        if ot_entry[0] == u'#':
          ot_entry = ot_entry[1:]
        object_type.append( ot_entry )
    if len( object_type ) > 0:
      return_val = object_type
    else:
      return_val = None
    return return_val





  def parseTitle(self):
    if self.parse_errors: return
    xpath = u't:teiHeader/t:fileDesc/t:titleStmt/t:title'
    element_list = self.xml_doc.xpath( xpath, namespaces=(self.namespace) )
    x = element_list[0].text
    assert type(x) == str, type(x)
    self.title = x.decode(u'utf-8', u'replace')
    return self.title

  def parseWriting(self):
    if self.parse_errors: return
    NS = {'t': 'http://www.tei-c.org/ns/1.0'}
    xpath = u't:teiHeader/t:fileDesc/t:sourceDesc/t:msDesc/t:physDesc/t:handDesc'
    element_list = self.xml_doc.xpath( xpath, namespaces=(NS) )
    if len( element_list ) > 0:
      element = element_list[0]
      assert type(element) == lxml.etree._Element, type(element)
      try:
        x = element.attrib[u'ana']
      except KeyError:
        return self.writing  # None
      x = x.decode( u'utf-8' )
      x = ( x[1:] if x[0] == u'#' else x )
      assert type(x) == unicode, type(x)
      self.writing = x
      return self.writing

  # end class Parser
