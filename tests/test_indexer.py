# -*- coding: utf-8 -*-

import logging, pprint, unittest
from usep_gh_handler_app.utils.indexer import Indexer


log = logging.getLogger(__name__)


class IndexerTest( unittest.TestCase ):
    """ Tests Indexer functions.
        To use:
        - activate the virtual environment
        - cd to tests directory
        - run python ./test_indexer.py """

    def test__build_solr_dict(self):
        """ Tests solr dict produced from xml file. """
        indexer = Indexer( log )
        solr_dict = indexer._build_solr_dict(
            inscription_xml_path=u'./test_files/CA.Berk.UC.HMA.G.8-4213.xml',
            bib_xml_path=u'./test_files/usepi_bib.xml' )
        print u'solr_dict...'; pprint.pprint( solr_dict )
        expected = [
            u'bib_authors',
            u'bib_ids',
            u'bib_ids_filtered',
            u'bib_ids_types',
            u'bib_titles',
            u'bib_titles_all',
            u'condition',
            u'decoration',
            u'fake',
            u'graphic_name',
            u'id',
            u'language',
            u'material',
            u'msid_idno',
            u'msid_institution',
            u'msid_region',
            u'msid_repository',
            u'msid_settlement',
            u'object_type',
            u'status',
            u'text_genre',
            u'title',
            u'writing']
        self.assertEqual( expected, sorted(solr_dict.keys()) )




if __name__ == "__main__":
  unittest.TestCase.maxDiff = None  # allows error to show in long output
  unittest.main()
