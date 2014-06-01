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

    def update_index_entry( self, updated_file_path ):
        """ Updates solr index for a new or changed file. """
        self.log.debug( u'in utils.indexer.update_index_entry(); updated_file_path, `%s`' % updated_file_path )
        full_file_path = u'%s/%s' % ( self.WEBSERVED_DATA_DIR_PATH, updated_file_path )
        file_name = updated_file_path.split('/')[-1]
        p = Parser( log )
        xml = open( x_entry ).read()
        d_xml = xml.replace( 'xmlns:', 'xmlnamespace:' )  # de-namespacing for easy element addressing
        pq = pq = PyQuery( d_xml )  # pq is now addressable w/jquery syntax


        self.solr_dict[u'id'] = p.i_id; assert not p.i_id == None
        self.solr_dict[u'bib_ids'] = p.bib_ids
        self.solr_dict[u'bib_ids_filtered'] = p.parseBibIdsFiltered()
        self.solr_dict[u'bib_ids_types'] = p.parseBibIdsTypes()
        self.solr_dict[u'title'] = p.parseTitle()
        ## sd-text_genre (we want, eg, 'verse' from <msItem class="#verse">)
        text_genre = []  # multi-valued
        tg_segments = pq('msitem').attr('class')
        if tg_segments:
          tg_segments = tg_segments.split()
          for tg_entry in tg_segments:
            tg_entry = tg_entry.strip()
            if tg_entry[0] == '#':
              tg_entry = tg_entry[1:]
            text_genre.append( tg_entry )
        if len( text_genre ) > 0:
          self.solr_dict[u'text_genre'] = text_genre
        ## sd-object_type
        object_type = []
        ot_segments = pq('objectdesc').attr('ana')
        if ot_segments:
          ot_segments = ot_segments.split()
          for ot_entry in ot_segments:
            ot_entry = ot_entry.strip()
            if ot_entry[0] == '#':
              ot_entry = ot_entry[1:]
            object_type.append( ot_entry )
        if len( object_type ) > 0:
          self.solr_dict[u'object_type'] = object_type
        ## sd-bib-title
        if not p.parse_errors: p.parseBibTitles()
        self.solr_dict[u'bib_titles'] = p.bib_titles
        self.solr_dict[u'bib_titles_all'] = p.bib_titles_all
        ## sd-bib-author
        p.parseBibAuthors()
        self.solr_dict[u'bib_authors'] = p.bib_authors
        ## sd-condition
        self.solr_dict[u'condition'] = p.parseCondition()
        ## sd-decoration
        self.solr_dict[u'decoration'] = p.parseDecoration()
        ## sd-fake
        self.solr_dict[u'fake'] = p.parseFake()

        ## sd-graphic_name
        self.solr_dict[u'graphic_name'] = p.parse_graphic_name()

        ## sd-language
        self.solr_dict[u'language'] = p.parseLanguage()
        ## sd-material
        self.solr_dict[u'material'] = p.parseMaterial()
        ## sd-msid fields
        self.solr_dict[u'msid_region'] = p.parseMsidRegion()
        self.solr_dict[u'msid_settlement'] = p.parseMsidSettlement()
        self.solr_dict[u'msid_institution'] = p.parseMsidInstitution()
        self.solr_dict[u'msid_repository'] = p.parseMsidRepository()
        self.solr_dict[u'msid_idno'] = p.parseMsidIdno()
        ## sd-status
        self.solr_dict[u'status'] = p.parseStatus()
        ## sd-writing
        self.solr_dict[u'writing'] = p.parseWriting()
        ## ok, build the file dict
        if not p.parse_errors:
          rd['id_list'].append( self.solr_dict[u'id'] )
          fdd['solr_data'] = sd
          rd['file_data'][ self.solr_dict[u'id'] ] = fdd
        # break  # for testing
        if p.parse_errors:
          self.bad_files_dict[file_name] = p.parse_errors
        rd[u'errors'] = self.bad_files_dict
        json_string = json.dumps( rd, sort_keys=False, indent=2 )
        self.file_data = json_string
        logger.debug( u'end of Updater.make_file_data(); self.bad_files_dict is: %s' % pprint.pformat(self.bad_files_dict) )
        logger.debug( u'end of Updater.make_file_data(); self.file_data json-string is: %s' % self.file_data )
        return self.file_data
        # end def make_file_data()

        pass

    def remove_index_entry( self ):
        """ Updates solr index for a removed file. """
        pass

    ## end class Indexer()


class Parser( object ):



## queue runners ##

def run_update_index( files_updated, files_removed ):
    """ Creates index jobs (doesn't actually call Indexer() directly.
        Triggered by utils.processor.run_copy_files(). """
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
